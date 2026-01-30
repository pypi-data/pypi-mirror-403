"""Dashboard rendering service using headless Chrome (pychrome + CDP)."""

import base64
import logging
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

import pychrome

logger = logging.getLogger(__name__)

# Configuration
CHROME_HOST = os.environ.get("CHROME_HOST", "127.0.0.1")
CHROME_PORT = int(os.environ.get("CHROME_PORT", "9222"))
CHROME_URL = f"http://{CHROME_HOST}:{CHROME_PORT}"

# Frontend URL for render routes
# In production (Cloud Run), backend serves SPA locally to avoid 60s Firebase Hosting latency
# Chrome loads from localhost:8080 instead of going through the internet
def _get_frontend_url() -> str:
    # Check if static files are available (production Docker image)
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    if os.path.exists(static_dir):
        # Use backend's own port for local SPA serving
        port = os.environ.get("PORT", "8080")
        return f"http://127.0.0.1:{port}"

    # Explicit override for custom setups
    env_url = os.environ.get("FRONTEND_URL")
    if env_url:
        return env_url

    # Local development: frontend dev server via Docker host
    return "http://host.docker.internal:5173"

FRONTEND_URL = _get_frontend_url()


@dataclass
class RenderResult:
    """Result of a render operation."""

    data: bytes
    format: Literal["png", "pdf"]
    width: int
    height: int


class RenderError(Exception):
    """Error during rendering."""

    pass


class ChromeConnectionError(RenderError):
    """Failed to connect to Chrome."""

    pass


class RenderTimeoutError(RenderError):
    """Render operation timed out."""

    pass


# -----------------------------------------------------------------------------
# Render Token Management (stored in Firestore for cross-process access)
# -----------------------------------------------------------------------------

from google.cloud import firestore


def _get_firestore_client() -> firestore.Client:
    """Get Firestore client, using emulator if configured."""
    import os
    emulator_host = os.environ.get("FIRESTORE_EMULATOR_HOST")
    if emulator_host:
        logger.info(f"Using Firestore emulator at {emulator_host}")
    else:
        logger.info("Using production Firestore")
    # Always specify project to avoid picking up wrong default from ADC
    return firestore.Client(project="metricly-dev")


def create_render_token(
    org_id: str,
    resource_type: Literal["dashboard", "widget"],
    resource_id: str,
    ttl_seconds: int = 120,
) -> str:
    """
    Create a short-lived, single-use token for render access.

    Tokens are stored in Firestore so they can be validated by any process
    (MCP server creates tokens, HTTP backend validates them).

    Args:
        org_id: Organization ID
        resource_type: Type of resource to render
        resource_id: ID of the resource (dashboard or widget)
        ttl_seconds: Token lifetime in seconds (default: 120)

    Returns:
        Token string
    """
    token = secrets.token_urlsafe(32)
    db = _get_firestore_client()

    db.collection("render_tokens").document(token).set({
        "org_id": org_id,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "expires": datetime.utcnow() + timedelta(seconds=ttl_seconds),
        "validated": False,
    })

    logger.info(f"Created render token for {resource_type}/{resource_id}, token={token[:20]}...")
    return token


def validate_render_token(
    token: str,
    resource_type: Literal["dashboard", "widget"],
    resource_id: str,
) -> str | None:
    """
    Validate a render token for initial page load.

    Args:
        token: Token to validate
        resource_type: Expected resource type
        resource_id: Expected resource ID

    Returns:
        org_id if valid, None otherwise
    """
    db = _get_firestore_client()
    doc_ref = db.collection("render_tokens").document(token)
    doc = doc_ref.get()

    if not doc.exists:
        logger.warning(f"Render token not found: {token[:20]}...")
        return None

    data = doc.to_dict()

    # Check expiry
    expires = data.get("expires")
    if expires:
        # Handle both datetime and Firestore Timestamp
        if hasattr(expires, "timestamp"):
            expires = datetime.utcfromtimestamp(expires.timestamp())
        if expires < datetime.utcnow():
            doc_ref.delete()
            logger.warning(f"Render token expired: {token[:20]}...")
            return None

    # Check resource matches
    if data.get("resource_type") != resource_type or data.get("resource_id") != resource_id:
        logger.warning(f"Render token resource mismatch: expected {resource_type}/{resource_id}")
        return None

    # Mark as validated (for subsequent query calls)
    doc_ref.update({"validated": True})
    logger.info(f"Validated render token for {resource_type}/{resource_id}")

    return data.get("org_id")


def validate_render_token_for_query(token: str) -> str | None:
    """
    Validate a render token for data queries during render session.

    Unlike validate_render_token, this doesn't check resource type/id,
    allowing the token to be used for metric queries.

    Args:
        token: Token to validate

    Returns:
        org_id if valid, None otherwise
    """
    db = _get_firestore_client()
    doc = db.collection("render_tokens").document(token).get()

    if not doc.exists:
        logger.warning(f"Render token not found for query: {token[:20]}...")
        return None

    data = doc.to_dict()

    # Check expiry
    expires = data.get("expires")
    if expires:
        # Handle both datetime and Firestore Timestamp
        if hasattr(expires, "timestamp"):
            expires = datetime.utcfromtimestamp(expires.timestamp())
        if expires < datetime.utcnow():
            db.collection("render_tokens").document(token).delete()
            logger.warning(f"Render token expired for query: {token[:20]}...")
            return None

    # Token must have been validated first (page was loaded)
    if not data.get("validated"):
        logger.warning(f"Render token not validated for query: {token[:20]}...")
        return None

    return data.get("org_id")


# -----------------------------------------------------------------------------
# Chrome/CDP Rendering
# -----------------------------------------------------------------------------


def _connect_to_chrome() -> pychrome.Browser:
    """Connect to headless Chrome via CDP."""
    try:
        return pychrome.Browser(url=CHROME_URL)
    except Exception as e:
        raise ChromeConnectionError(f"Failed to connect to Chrome at {CHROME_URL}: {e}")


def render_url_to_png(
    url: str,
    width: int = 1200,
    height: int = 800,
    timeout_seconds: int = 60,
    wait_selector: str | None = None,
    full_page: bool = False,
) -> bytes:
    """
    Render a URL to PNG image.

    Args:
        url: URL to render
        width: Viewport width
        height: Viewport height
        timeout_seconds: Maximum time to wait
        wait_selector: CSS selector to wait for before capture
        full_page: Capture full page (scrollable) instead of viewport

    Returns:
        PNG image bytes
    """
    logger.info(f"Rendering URL to PNG: {url}")
    browser = _connect_to_chrome()
    tab = None

    try:
        tab = browser.new_tab()
        tab.start()
        logger.info("Chrome tab created and started")

        # Set viewport size
        tab.call_method(
            "Emulation.setDeviceMetricsOverride",
            width=width,
            height=height,
            deviceScaleFactor=2,  # Retina quality
            mobile=False,
        )

        # Enable required domains
        tab.call_method("Page.enable")
        tab.call_method("Runtime.enable")

        # Navigate
        logger.info(f"Navigating to: {url}")
        tab.call_method("Page.navigate", url=url, _timeout=timeout_seconds)

        # Wait for page load
        logger.info("Waiting for initial page load...")
        tab.wait(2)  # Initial wait

        # Wait for specific selector if provided
        if wait_selector:
            logger.info(f"Waiting for selector: {wait_selector}")
            _wait_for_selector(tab, wait_selector, timeout_seconds)
            logger.info("Selector found or timeout")

        # Capture screenshot
        logger.info("Capturing screenshot...")
        if full_page:
            # Get full page dimensions
            layout = tab.call_method("Page.getLayoutMetrics")
            content_size = layout.get("contentSize", {})
            full_width = int(content_size.get("width", width))
            full_height = int(content_size.get("height", height))

            # Update viewport to full page
            tab.call_method(
                "Emulation.setDeviceMetricsOverride",
                width=full_width,
                height=full_height,
                deviceScaleFactor=2,
                mobile=False,
            )
            tab.wait(0.5)

        result = tab.call_method("Page.captureScreenshot", format="png")
        png_data = base64.b64decode(result["data"])
        logger.info(f"Screenshot captured, size: {len(png_data)} bytes")
        return png_data

    except pychrome.TimeoutException as e:
        raise RenderTimeoutError(f"Render timed out: {e}")
    except Exception as e:
        raise RenderError(f"Render failed: {e}")
    finally:
        if tab:
            try:
                tab.stop()
                browser.close_tab(tab)
            except Exception:
                pass


def render_url_to_pdf(
    url: str,
    timeout_seconds: int = 60,
    wait_selector: str | None = None,
    landscape: bool = True,
    print_background: bool = True,
    paper_width: float = 11,  # inches (Letter landscape)
    paper_height: float = 8.5,
) -> bytes:
    """
    Render a URL to PDF.

    Args:
        url: URL to render
        timeout_seconds: Maximum time to wait
        wait_selector: CSS selector to wait for before capture
        landscape: Use landscape orientation
        print_background: Include background colors/images
        paper_width: Paper width in inches
        paper_height: Paper height in inches

    Returns:
        PDF bytes
    """
    browser = _connect_to_chrome()
    tab = None

    try:
        tab = browser.new_tab()
        tab.start()

        # Enable required domains
        tab.call_method("Page.enable")
        tab.call_method("Runtime.enable")

        # Navigate
        tab.call_method("Page.navigate", url=url, _timeout=timeout_seconds)

        # Wait for page load
        tab.wait(2)

        # Wait for specific selector if provided
        if wait_selector:
            _wait_for_selector(tab, wait_selector, timeout_seconds)

        # Generate PDF
        result = tab.call_method(
            "Page.printToPDF",
            landscape=landscape,
            printBackground=print_background,
            paperWidth=paper_width,
            paperHeight=paper_height,
            marginTop=0.4,
            marginBottom=0.4,
            marginLeft=0.4,
            marginRight=0.4,
        )
        return base64.b64decode(result["data"])

    except pychrome.TimeoutException as e:
        raise RenderTimeoutError(f"Render timed out: {e}")
    except Exception as e:
        raise RenderError(f"Render failed: {e}")
    finally:
        if tab:
            try:
                tab.stop()
                browser.close_tab(tab)
            except Exception:
                pass


def _wait_for_selector(tab, selector: str, timeout_seconds: int) -> bool:
    """Wait for a CSS selector to appear in the page.

    Returns True if selector was found, False if timed out.
    """
    js_code = f"""
    new Promise((resolve, reject) => {{
        const timeout = setTimeout(() => resolve(false), {timeout_seconds * 1000});
        const check = () => {{
            if (document.querySelector('{selector}')) {{
                clearTimeout(timeout);
                resolve(true);
            }} else {{
                requestAnimationFrame(check);
            }}
        }};
        check();
    }})
    """
    try:
        result = tab.call_method(
            "Runtime.evaluate",
            expression=js_code,
            awaitPromise=True,
            _timeout=timeout_seconds + 5,  # Extra buffer for CDP timeout
        )
        found = result.get("result", {}).get("value", False)
        if not found:
            logger.warning(f"Selector '{selector}' not found within {timeout_seconds}s, proceeding anyway")
        return found
    except Exception as e:
        logger.warning(f"Selector wait failed: {e}, proceeding anyway")
        return False


# -----------------------------------------------------------------------------
# High-level render functions
# -----------------------------------------------------------------------------


def render_dashboard(
    org_id: str,
    dashboard_id: str,
    page_id: str | None = None,
    format: Literal["png", "pdf"] = "pdf",
    width: int = 1200,
    height: int = 800,
) -> RenderResult:
    """
    Render a dashboard to PNG or PDF.

    Args:
        org_id: Organization ID
        dashboard_id: Dashboard ID to render
        page_id: Optional page ID to render (if None, renders all pages)
        format: Output format
        width: Viewport width (for PNG)
        height: Viewport height (for PNG)

    Returns:
        RenderResult with binary data
    """
    # Create render token
    token = create_render_token(org_id, "dashboard", dashboard_id)

    # Build render URL
    render_url = f"{FRONTEND_URL}/render/dashboard/{dashboard_id}?token={token}"
    if page_id:
        render_url += f"&page={page_id}"
    logger.info(f"Render URL: {render_url}")

    # Render - wait for data-render-ready="true" which signals all widgets loaded
    wait_selector = '[data-render-ready="true"]'

    if format == "pdf":
        data = render_url_to_pdf(render_url, wait_selector=wait_selector)
    else:
        data = render_url_to_png(
            render_url, width=width, height=height, wait_selector=wait_selector, full_page=True
        )

    return RenderResult(data=data, format=format, width=width, height=height)


def render_widget(
    org_id: str,
    dashboard_id: str,
    widget_id: str,
    width: int = 600,
    height: int = 400,
) -> RenderResult:
    """
    Render a single widget to PNG.

    Args:
        org_id: Organization ID
        dashboard_id: Dashboard containing the widget
        widget_id: Widget ID to render
        width: Viewport width
        height: Viewport height

    Returns:
        RenderResult with PNG data
    """
    # Create render token
    token = create_render_token(org_id, "widget", f"{dashboard_id}/{widget_id}")

    # Build render URL
    render_url = f"{FRONTEND_URL}/render/widget/{dashboard_id}/{widget_id}?token={token}"

    # Render as PNG - wait for data-render-ready="true" which signals widget loaded
    data = render_url_to_png(
        render_url,
        width=width,
        height=height,
        wait_selector='[data-render-ready="true"]',
    )

    return RenderResult(data=data, format="png", width=width, height=height)
