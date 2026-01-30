"""Chat with Data - Pydantic AI agent for natural language metric queries."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Any, Callable, Awaitable

from pydantic import BaseModel, Field, ValidationError
from pydantic_ai import Agent, RunContext

from settings import get_settings
import storage
from services import queries as query_service
from services import manifest as manifest_service
from services.auth import UserContext
from generated.format_types import FormatDefinition
from generated.widget_types import WidgetType, Grain, Orientation, QueryParams as GeneratedQueryParams
from generated.dashboard_types import DashboardDefinition
from pathlib import Path


def strip_null_values(obj: Any) -> Any:
    """
    Recursively strip null values from a dictionary/list structure.
    This is necessary because Pydantic structured output includes all optional fields
    as null, but we want to compare against the original which only has non-null values.
    """
    if isinstance(obj, dict):
        return {k: strip_null_values(v) for k, v in obj.items() if v is not None}
    elif isinstance(obj, list):
        return [strip_null_values(item) for item in obj]
    else:
        return obj


def fix_dashboard_immutable_fields(dashboard: dict[str, Any], original: dict[str, Any]) -> dict[str, Any]:
    """
    Fix immutable fields in the LLM-generated dashboard by copying from the original.
    This is necessary because the LLM cannot perfectly reproduce timestamps and IDs.
    """
    now = datetime.now().isoformat()

    # Copy immutable fields from original (with sensible defaults if missing)
    dashboard['id'] = original.get('id') or dashboard.get('id') or 'unknown'
    dashboard['owner'] = original.get('owner') or dashboard.get('owner') or 'unknown'
    dashboard['created_at'] = original.get('created_at') or dashboard.get('created_at') or now
    dashboard['created_by'] = original.get('created_by') or dashboard.get('created_by') or 'unknown'
    dashboard['visibility'] = original.get('visibility') or dashboard.get('visibility') or 'private'
    dashboard['version'] = original.get('version') or dashboard.get('version')

    # Set updated_at to current time
    dashboard['updated_at'] = now

    # If controls is missing or incomplete, copy from original
    if 'controls' not in dashboard or not isinstance(dashboard.get('controls'), dict):
        dashboard['controls'] = original.get('controls')

    return dashboard


def validate_dashboard_update(dashboard: dict[str, Any] | None, original: dict[str, Any] | None) -> list[str]:
    """
    Validate a dashboard_update response against the Pydantic schema.
    Returns a list of validation errors, or empty list if valid.
    Note: Call fix_dashboard_immutable_fields first to fix immutable fields.
    """
    if dashboard is None:
        return []  # No dashboard_update to validate

    # Use Pydantic schema validation - this is the single source of truth
    try:
        DashboardDefinition.model_validate(dashboard)
        return []
    except ValidationError as e:
        issues: list[str] = []
        for error in e.errors():
            loc = '.'.join(str(x) for x in error['loc'])
            issues.append(f"{loc}: {error['msg']}")
        return issues

# Load prompts from generated schema documentation
_SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
_FORMAT_PROMPT: str | None = None
_WIDGET_PROMPT: str | None = None
_DASHBOARD_PROMPT: str | None = None


def _get_format_prompt() -> str:
    """Load the format prompt from the generated schema documentation."""
    global _FORMAT_PROMPT
    if _FORMAT_PROMPT is None:
        path = _SCHEMAS_DIR / "format.prompt.md"
        if path.exists():
            _FORMAT_PROMPT = path.read_text()
        else:
            _FORMAT_PROMPT = "Format types: number, currency, percent, percent_value, date, compact, duration"
    return _FORMAT_PROMPT


def _get_widget_prompt() -> str:
    """Load the widget prompt from the generated schema documentation."""
    global _WIDGET_PROMPT
    if _WIDGET_PROMPT is None:
        path = _SCHEMAS_DIR / "widget.prompt.md"
        if path.exists():
            _WIDGET_PROMPT = path.read_text()
        else:
            _WIDGET_PROMPT = "Widget types: kpi, line_chart, area_chart, bar_chart, donut, table"
    return _WIDGET_PROMPT


def _get_dashboard_prompt() -> str:
    """Load the dashboard prompt from the generated schema documentation."""
    global _DASHBOARD_PROMPT
    if _DASHBOARD_PROMPT is None:
        path = _SCHEMAS_DIR / "dashboard.prompt.md"
        if path.exists():
            _DASHBOARD_PROMPT = path.read_text()
        else:
            _DASHBOARD_PROMPT = "Dashboard structure: pages > sections > widgets"
    return _DASHBOARD_PROMPT

from metricflow.engine.metricflow_engine import MetricFlowEngine


# ============================================================================
# Request/Response Models
# ============================================================================

class QueryParams(BaseModel):
    """Parameters for a metric query."""
    metrics: list[str] = Field(description="List of metric names to query")
    dimensions: list[str] | None = Field(default=None, description="Dimensions to group by")
    grain: Literal["day", "week", "month", "quarter", "year"] | None = Field(
        default=None, description="Time granularity for the query"
    )
    start_date: str | None = Field(default=None, description="Start date in YYYY-MM-DD format")
    end_date: str | None = Field(default=None, description="End date in YYYY-MM-DD format")
    limit: int | None = Field(default=None, description="Maximum number of rows to return")
    order_by: str | None = Field(default=None, description="Column to sort by, append ' desc' for descending (e.g. 'total_revenue desc')")


class VisualizationConfig(BaseModel):
    """Configuration for visualizing query results."""
    type: Literal["area_chart", "bar_chart", "line_chart", "donut", "kpi", "table"] = Field(
        description="Chart type for visualization"
    )
    title: str = Field(description="Title for the visualization")
    query: QueryParams = Field(description="Query that produced this data")
    orientation: Literal["horizontal", "vertical"] | None = Field(
        default=None, description="Bar chart orientation (vertical for categories, horizontal for rankings)"
    )


# FormatConfig is now imported from generated.format_types as FormatDefinition
# Using the schema-generated type ensures consistency across frontend/backend/LLM


class WidgetUpdate(BaseModel):
    """Updated widget configuration."""
    type: Literal["area_chart", "bar_chart", "line_chart", "donut", "kpi", "table"] = Field(
        description="Widget type"
    )
    title: str = Field(description="Widget title")
    query: QueryParams = Field(description="Query configuration")
    format: FormatDefinition | None = Field(
        default=None, description="Value formatting - IMPORTANT: set this appropriately for the metric type"
    )
    orientation: Literal["horizontal", "vertical"] | None = Field(
        default=None, description="Bar chart orientation"
    )
    time_scope: Literal["range", "latest", "latest_complete"] | None = Field(
        default=None,
        description="Date scope for non-time-series widgets: 'range' (full date range), 'latest' (current period), 'latest_complete' (last complete period)"
    )


class DashboardAction(BaseModel):
    """Action to perform on the dashboard."""
    action: Literal["add_widget"] = Field(description="Type of action")
    page_id: str = Field(description="ID of the page to add the widget to")
    section_index: int = Field(description="Index of the section to add the widget to")
    widget: WidgetUpdate = Field(description="Widget configuration to add")


class ChatResponse(BaseModel):
    """Structured response from the chat agent."""
    answer: str = Field(description="Natural language answer to the user's question")
    visualization: VisualizationConfig | None = Field(
        default=None, description="Visualization config if data was queried"
    )
    data: list[dict[str, Any]] | None = Field(
        default=None, description="Query result data if applicable"
    )
    widget_update: WidgetUpdate | None = Field(
        default=None, description="Updated widget configuration when modifying an existing widget"
    )
    dashboard_action: DashboardAction | None = Field(
        default=None, description="Action to perform on the dashboard (e.g., add widget)"
    )
    dashboard_update: DashboardDefinition | None = Field(
        default=None, description="Full modified dashboard definition for structural changes (add/remove/reorder widgets, sections, pages)"
    )


class WidgetContextPayload(BaseModel):
    """Current widget being edited."""
    widget: dict[str, Any]
    dashboard_controls: dict[str, Any] | None = None  # Current dashboard date/grain settings
    rendered_data: list[dict[str, Any]] | None = None  # Actual data currently shown in widget


class DashboardSectionInfo(BaseModel):
    """Section info for dashboard context."""
    title: str | None = None
    widget_count: int


class DashboardPageInfo(BaseModel):
    """Page info for dashboard context."""
    id: str
    title: str
    sections: list[DashboardSectionInfo]


class DashboardControlsInfo(BaseModel):
    """Current dashboard control settings."""
    date_range: dict[str, str]  # from, to
    grain: str


class DashboardContextPayload(BaseModel):
    """Dashboard structure for adding widgets."""
    pages: list[DashboardPageInfo]
    controls: DashboardControlsInfo | None = None


class ChatRequest(BaseModel):
    """Request for the chat endpoint."""
    message: str
    history: list[dict[str, str]] | None = None  # Previous messages
    widget_context: WidgetContextPayload | None = None  # Widget being edited
    dashboard_context: DashboardContextPayload | None = None  # Dashboard structure
    full_dashboard: dict[str, Any] | None = None  # Full dashboard JSON for manipulation


# ============================================================================
# Metric CRUD Models
# ============================================================================

class MetricTypeParams(BaseModel):
    """Type parameters for a metric."""
    measure: str | None = Field(default=None, description="Measure name for simple metrics")
    numerator: str | None = Field(default=None, description="Numerator metric for ratio/derived")
    denominator: str | None = Field(default=None, description="Denominator metric for ratio/derived")
    expr: str | None = Field(default=None, description="Expression for derived metrics")
    metrics: list[str] | None = Field(default=None, description="Metrics list for derived metrics")


class CreateMetricParams(BaseModel):
    """Parameters for creating a new metric."""
    name: str = Field(description="Unique metric name (snake_case)")
    description: str = Field(description="Human-readable description of what the metric measures")
    type: Literal["simple", "ratio", "derived"] = Field(description="Metric type")
    label: str | None = Field(default=None, description="Display label for the metric")
    type_params: MetricTypeParams = Field(description="Type-specific parameters")


class UpdateMetricParams(BaseModel):
    """Parameters for updating an existing metric."""
    description: str | None = Field(default=None, description="Updated description")
    label: str | None = Field(default=None, description="Updated display label")
    type_params: MetricTypeParams | None = Field(default=None, description="Updated type parameters")


# ============================================================================
# Semantic Model CRUD Models
# ============================================================================

class EntityDefinition(BaseModel):
    """An entity (join key) in a semantic model."""
    name: str = Field(description="Entity name")
    type: Literal["primary", "foreign", "unique", "natural"] = Field(description="Entity type")
    expr: str | None = Field(default=None, description="SQL expression for the entity")


class DimensionDefinition(BaseModel):
    """A dimension in a semantic model."""
    name: str = Field(description="Dimension name")
    type: Literal["categorical", "time"] = Field(description="Dimension type")
    expr: str | None = Field(default=None, description="SQL expression for the dimension")
    type_params: dict | None = Field(default=None, description="Type-specific parameters (e.g., time_granularity for time dimensions)")


class MeasureDefinition(BaseModel):
    """A measure in a semantic model."""
    name: str = Field(description="Measure name")
    agg: Literal["sum", "count", "count_distinct", "average", "min", "max", "sum_boolean", "median", "percentile"] = Field(
        description="Aggregation type"
    )
    expr: str | None = Field(default=None, description="SQL expression for the measure")
    description: str | None = Field(default=None, description="Human-readable description")
    create_metric: bool | None = Field(default=None, description="Whether to auto-create a metric for this measure")


class CreateSemanticModelParams(BaseModel):
    """Parameters for creating a new semantic model."""
    name: str = Field(description="Unique model name (snake_case)")
    description: str | None = Field(default=None, description="Human-readable description")
    model: str = Field(description="Reference to the underlying dbt model or table (e.g., 'ref(\"my_table\")')")
    entities: list[EntityDefinition] | None = Field(default=None, description="Entity definitions (join keys)")
    dimensions: list[DimensionDefinition] | None = Field(default=None, description="Dimension definitions")
    measures: list[MeasureDefinition] | None = Field(default=None, description="Measure definitions")


class UpdateSemanticModelParams(BaseModel):
    """Parameters for updating an existing semantic model."""
    description: str | None = Field(default=None, description="Updated description")
    model: str | None = Field(default=None, description="Updated model reference")
    entities: list[EntityDefinition] | None = Field(default=None, description="Updated entities (replaces all)")
    dimensions: list[DimensionDefinition] | None = Field(default=None, description="Updated dimensions (replaces all)")
    measures: list[MeasureDefinition] | None = Field(default=None, description="Updated measures (replaces all)")


# ============================================================================
# Dependencies
# ============================================================================

@dataclass
class ChatDependencies:
    """Dependencies injected into the chat agent."""
    mf_engine: MetricFlowEngine
    bq_client: Any  # BigQuery client for query execution
    semantic_manifest: Any  # The semantic manifest for metric lookups
    tenant_context: str  # Condensed context string for the system prompt
    query_executor: Any  # ThreadPoolExecutor for running queries
    org_id: str  # Organization ID for CRUD operations
    user_id: str  # User ID for provenance tracking
    user_email: str = ""  # User email for service layer
    user_role: str = "viewer"  # User role for service layer permission checks
    org_name: str = ""  # Organization name for display
    widget_context: dict[str, Any] | None = None  # Current widget being edited
    widget_dashboard_controls: dict[str, Any] | None = None  # Dashboard controls when editing widget
    widget_rendered_data: list[dict[str, Any]] | None = None  # Actual data shown in widget
    dashboard_context: DashboardContextPayload | None = None  # Dashboard structure (for simple add_widget)
    full_dashboard: dict[str, Any] | None = None  # Full dashboard JSON for dashboard_update responses
    status_callback: Callable[[str], Awaitable[None]] | None = None  # Callback for status updates
    user_preferences: dict[str, Any] | None = None  # User preferences for personalization


def _get_user_context(deps: ChatDependencies) -> UserContext:
    """Create a UserContext from ChatDependencies for service layer calls."""
    return UserContext(
        uid=deps.user_id,
        email=deps.user_email,
        org_id=deps.org_id,
        org_name=deps.org_name or deps.org_id,  # Fall back to org_id if name not set
        role=deps.user_role,  # type: ignore[arg-type]
    )


async def emit_status(deps: ChatDependencies, status: str) -> None:
    """Emit a status update if callback is configured."""
    if deps.status_callback:
        await deps.status_callback(status)


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = """You are a data analyst assistant for a business intelligence dashboard. You help users understand their business metrics, answer questions about their data, and manage the metric definitions.

## YOUR CAPABILITIES

1. **Answer Data Questions**: Query metrics and provide insights
2. **Explain Metrics**: Describe what metrics measure and how they're calculated
3. **Create Visualizations**: Suggest appropriate chart types for data
4. **Manage Metrics**: Create, update, and delete metric definitions

## TOOLS

### Query Tools
- `query_metrics`: Execute a query against the semantic layer. Use this to fetch actual data.
- `explain_metric`: Get the definition and calculation logic for a specific metric.

### Metric Management Tools
- `list_semantic_models`: List all semantic models in the organization.
- `list_metrics`: List all metric definitions with their types and descriptions.
- `create_metric`: Create a new metric definition. Requires name, type, and type_params.
- `update_metric`: Update an existing metric's description, label, or type parameters.
- `delete_metric`: Delete a metric definition. Only metrics created in Metricly can be deleted.
- `preview_metric`: Preview query results for a metric before saving changes.

## GUIDELINES

1. **Always query data** when the user asks a quantitative question (how much, how many, what is, etc.)
2. **Be concise** - provide direct answers with key insights
3. **Suggest visualizations** when you query time-series or categorical data
4. **Use appropriate grain**:
   - For recent periods (last week/month): use day or week grain
   - For longer periods (quarter/year): use month grain
5. **Include comparisons** when relevant (vs last period, YoY, etc.)

{widget_types}

## WIDGET TITLE GUIDELINES

IMPORTANT: Never include grain/time period words in widget titles:
- BAD: "Monthly Revenue", "Daily Orders", "Weekly Active Users", "Q1 Sales"
- GOOD: "Revenue", "Orders", "Active Users", "Sales", "Revenue Over Time"

Why: Dashboard grain is dynamic - users can switch between day/week/month/quarter.
A title like "Monthly Revenue" becomes misleading when the user selects daily grain.

## BAR CHART BEST PRACTICES

For bar charts comparing categories:
1. Always set `orientation: "vertical"` (categories on x-axis, values on y-axis)
2. Always sort by the metric descending: `order_by: "metric_name desc"`
3. Consider using `limit` to show top N items for cleaner visualization

Example query for "Top 10 Products by Revenue":
- metrics: ["total_revenue"]
- dimensions: ["product_name"]
- orientation: "vertical"
- order_by: "total_revenue desc"
- limit: 10

## CUMULATIVE/YTD METRICS

IMPORTANT: Cumulative metrics (YTD, running totals, metrics with names like `ytd_*` or `cumulative_*`) MUST use `grain: "day"`:
- MetricFlow uses FIRST_VALUE when aggregating cumulative metrics to coarser grains (week/month/quarter)
- This returns the FIRST day's running total, not the LAST day's (which is what users expect)
- Example: `ytd_total_revenue` at monthly grain for January returns Jan 1's YTD (~0), not Jan 31's YTD (~3.6M)
- Always use daily grain for cumulative metrics to show correct values

## RESPONSE FORMAT

After querying data, always:
1. State the key finding clearly
2. Provide brief context or insight
3. Include a visualization config if the data is visualizable

## WIDGET EDITING MODE

When `widget_context` is provided, you are editing an existing widget. In this mode:
1. The user wants to modify the current widget configuration
2. Return a `widget_update` with the modified configuration
3. Keep unchanged properties from the original widget
4. Common modifications:
   - "Change to bar chart" → update type to "bar_chart"
   - "Show last 6 months" → update grain to "month", adjust date range
   - "Add dimension X" → add to dimensions list
   - "Rename to Y" → update title

IMPORTANT: If the user says something "looks wrong" or asks about data issues:
- ALWAYS use query_metrics to fetch the actual data first
- Don't assume or guess what the values are - verify by querying
- Check the underlying components (e.g., for contribution_margin_pct, query total_revenue, cogs, labor_cost separately)
- Never claim data is correct without actually querying it

## RESPONSE TYPE SELECTION

Choose the correct response type based on what the user is asking for:

### Use `widget_update` when:
- User is in widget edit mode (widget_context is provided)
- Changing a single widget's type, title, query, format, or orientation
- Modifying the currently selected widget only

### Use `dashboard_action` (with action="add_widget") when:
- Adding a SINGLE new widget to a specific location
- User says something like "Add a revenue chart to Overview"
- Simple addition that doesn't require moving or removing other widgets

### Use `dashboard_update` when:
- Adding MULTIPLE widgets at once
- Removing widgets from the dashboard
- Moving widgets between sections or pages
- Reordering widgets within a section
- Adding, removing, or renaming pages or sections
- Any STRUCTURAL reorganization ("move all KPIs to a new section", "reorganize by metric type")
- Bulk operations that affect multiple elements

## DASHBOARD MANIPULATION SAFETY

When returning `dashboard_update`, you MUST follow these rules:

### REQUIRED TOP-LEVEL FIELDS (all mandatory, copy from original)
The dashboard_update MUST include ALL of these fields:
- id: string (copy exactly from original dashboard)
- title: string (copy unless user asks to rename)
- description: string or null (copy from original)
- owner: string (copy exactly from original)
- visibility: "private" | "org" (copy exactly from original)
- controls: object (copy exactly from original)
- pages: array (modified as needed)
- created_at: string (copy exactly from original, never change)
- updated_at: string (set to current ISO timestamp)
- created_by: string (copy exactly from original, never change)
- version: number (copy from original)

### PRESERVE Existing Content
- PRESERVE all widget IDs - never regenerate IDs for existing widgets
- PRESERVE all page and section IDs
- PRESERVE widgets the user didn't ask to change
- Copy all metadata fields EXACTLY from the original dashboard

### Only Modify What Was Requested
- Only add/remove/move elements explicitly requested by the user
- Keep pages, sections, and widgets in their original order unless reorganizing
- Do not "clean up" or "improve" parts of the dashboard not mentioned

### Generate New IDs for New Elements
- Use UUIDs for new widgets, sections, and pages
- Update `updated_at` to current timestamp

### Return the COMPLETE Dashboard
- `dashboard_update` REPLACES the entire dashboard
- Include ALL pages, sections, and widgets - not just the changed ones
- Missing elements will be DELETED

## DASHBOARD MODIFICATION MODE

When `dashboard_context` is provided (simple mode), you can add widgets to the dashboard. If the user asks to:
- "Add a revenue chart to Overview" → return a `dashboard_action` with action="add_widget"
- Specify the correct page_id and section_index based on the dashboard structure
- The widget configuration should include type, title, and query

When `full_dashboard` is provided (full edit mode), you can make structural changes:
- See the "RESPONSE TYPE SELECTION" section above for when to use each response type
- The frontend will show the user a diff and ask for confirmation before applying changes

{context}
"""


# ============================================================================
# Agent Definition (lazy-loaded to avoid requiring API key at import time)
# ============================================================================

_agent: Agent[ChatDependencies, ChatResponse] | None = None


def get_agent() -> Agent[ChatDependencies, ChatResponse]:
    """Get or create the chat agent (lazy initialization)."""
    global _agent
    if _agent is None:
        import os
        settings = get_settings()

        # Ensure API key is in environment for pydantic-ai
        if settings.anthropic_api_key and not os.environ.get("ANTHROPIC_API_KEY"):
            os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key

        _agent = Agent(
            "anthropic:claude-sonnet-4-5",
            deps_type=ChatDependencies,
            output_type=ChatResponse,
            instructions=SYSTEM_PROMPT,
        )
        # Register tools
        _register_tools(_agent)
    return _agent


def _register_tools(agent: Agent[ChatDependencies, ChatResponse]) -> None:
    """Register tools on the agent."""

    @agent.tool
    async def query_metrics_tool(ctx: RunContext[ChatDependencies], params: QueryParams) -> dict:
        """Execute a MetricFlow query and return the results.

        Use this tool to fetch actual data for metrics. You can query one or more metrics,
        optionally grouped by dimensions and/or time grain.
        """
        await emit_status(ctx.deps, "Querying data warehouse...")

        # Convert chat QueryParams to service QueryParams
        from datetime import date
        service_params = query_service.QueryParams(
            metrics=params.metrics,
            dimensions=params.dimensions,
            grain=params.grain,
            start_date=date.fromisoformat(params.start_date) if params.start_date else None,
            end_date=date.fromisoformat(params.end_date) if params.end_date else None,
            limit=params.limit or 100,  # Default limit for chat queries
            order_by=params.order_by,
        )

        try:
            result = await query_service.query_metrics(
                ctx.deps.org_id,
                service_params,
                include_visualization=False,
            )
            return {"data": result.data, "columns": result.columns, "error": None}
        except Exception as e:
            return {"data": [], "columns": [], "error": str(e)}

    @agent.tool
    async def explain_metric_tool(ctx: RunContext[ChatDependencies], metric_name: str) -> str:
        """Get the definition and calculation logic for a specific metric.

        Use this tool when the user asks what a metric means, how it's calculated,
        or wants to understand a metric better.
        """
        await emit_status(ctx.deps, "Looking up metric definition...")

        try:
            result = await query_service.explain_metric(ctx.deps.org_id, metric_name)

            # Format result as a readable string for the chat agent
            description = result.get("description", "No description available")
            metric_type = result.get("type", "unknown")

            calc_info = ""
            if "expression" in result:
                calc_info = f"\n\nCalculation: {result['expression']}"
            elif "measure" in result:
                calc_info = f"\n\nMeasure: {result['measure']}"

            return f"""**{metric_name}**

{description}

Type: {metric_type}{calc_info}"""

        except ValueError as e:
            return str(e)

    # -------------------------------------------------------------------------
    # Semantic Model Management Tools
    # -------------------------------------------------------------------------

    @agent.tool
    async def list_semantic_models_tool(ctx: RunContext[ChatDependencies]) -> list[dict]:
        """List all semantic models in the organization.

        Returns a list of semantic models with their names, descriptions, entities, dimensions, and measures.
        Use this to understand what data sources are available for metrics.
        """
        await emit_status(ctx.deps, "Exploring available data sources...")
        user = _get_user_context(ctx.deps)
        return await manifest_service.list_semantic_models(user)

    @agent.tool
    async def get_semantic_model_tool(ctx: RunContext[ChatDependencies], model_name: str) -> dict:
        """Get detailed information about a specific semantic model.

        Args:
            model_name: The name of the semantic model to retrieve.

        Returns:
            The semantic model definition or an error if not found.
        """
        user = _get_user_context(ctx.deps)
        try:
            return await manifest_service.get_semantic_model(user, model_name)
        except ValueError as e:
            return {"error": str(e)}

    @agent.tool
    async def create_semantic_model_tool(
        ctx: RunContext[ChatDependencies], params: CreateSemanticModelParams
    ) -> dict:
        """Create a new semantic model.

        Semantic models define the entities, dimensions, and measures that can be
        used for metrics. They map to underlying database tables.

        Args:
            params: The semantic model configuration.

        Returns:
            The created semantic model or an error message.
        """
        await emit_status(ctx.deps, "Creating semantic model...")

        # Build model document
        model_doc = {
            "name": params.name,
            "model": params.model,
        }
        if params.description:
            model_doc["description"] = params.description
        if params.entities:
            model_doc["entities"] = [e.model_dump(exclude_none=True) for e in params.entities]
        if params.dimensions:
            model_doc["dimensions"] = [d.model_dump(exclude_none=True) for d in params.dimensions]
        if params.measures:
            model_doc["measures"] = [m.model_dump(exclude_none=True) for m in params.measures]

        user = _get_user_context(ctx.deps)
        try:
            result = await manifest_service.create_semantic_model(user, model_doc)
            return {"success": True, "semantic_model": result}
        except ValueError as e:
            # Model already exists or validation failed
            return {"error": str(e)}
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    @agent.tool
    async def update_semantic_model_tool(
        ctx: RunContext[ChatDependencies], model_name: str, updates: UpdateSemanticModelParams
    ) -> dict:
        """Update an existing semantic model.

        Note: Only semantic models created in Metricly can have all fields updated.
        Imported models from dbt can only have description updated.

        Args:
            model_name: The name of the semantic model to update.
            updates: The fields to update. Arrays (entities, dimensions, measures) replace all existing values.

        Returns:
            The updated semantic model or an error message.
        """
        await emit_status(ctx.deps, "Updating semantic model...")

        # Build updates dict
        update_dict = {}
        if updates.description is not None:
            update_dict["description"] = updates.description
        if updates.model is not None:
            update_dict["model"] = updates.model
        if updates.entities is not None:
            update_dict["entities"] = [e.model_dump(exclude_none=True) for e in updates.entities]
        if updates.dimensions is not None:
            update_dict["dimensions"] = [d.model_dump(exclude_none=True) for d in updates.dimensions]
        if updates.measures is not None:
            update_dict["measures"] = [m.model_dump(exclude_none=True) for m in updates.measures]

        if not update_dict:
            return {"error": "No updates provided."}

        user = _get_user_context(ctx.deps)
        try:
            result = await manifest_service.update_semantic_model(user, model_name, update_dict)
            return {"success": True, "semantic_model": result}
        except ValueError as e:
            # Model not found
            return {"error": str(e)}
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    @agent.tool
    async def delete_semantic_model_tool(ctx: RunContext[ChatDependencies], model_name: str) -> dict:
        """Delete a semantic model.

        Note: Only semantic models created in Metricly can be deleted.
        Imported models from dbt cannot be deleted (they will reappear on next import).
        Deleting a semantic model may break metrics that reference its measures.

        Args:
            model_name: The name of the semantic model to delete.

        Returns:
            Success status or an error message.
        """
        await emit_status(ctx.deps, "Deleting semantic model...")

        user = _get_user_context(ctx.deps)

        # Check if model exists and get its origin for warning message
        try:
            existing = await manifest_service.get_semantic_model(user, model_name)
        except ValueError as e:
            return {"error": str(e)}

        # Warn about imported models (they'll reappear on next import)
        is_imported = existing.get("_origin") == "imported"

        try:
            await manifest_service.delete_semantic_model(user, model_name)
            if is_imported:
                return {
                    "warning": f"Semantic model '{model_name}' was imported from dbt. "
                    "Deleting it will only remove it until the next manifest import.",
                    "deleted": True,
                }
            return {"success": True}
        except ValueError as e:
            return {"error": str(e)}
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Metric Management Tools
    # -------------------------------------------------------------------------

    @agent.tool
    async def list_metrics_tool(ctx: RunContext[ChatDependencies]) -> list[dict]:
        """List all metric definitions in the organization.

        Returns a list of metrics with their names, types, descriptions, and labels.
        Use this when the user asks what metrics are available or wants to browse metrics.
        """
        await emit_status(ctx.deps, "Loading available metrics...")

        # Use the query service to list metrics from the semantic manifest
        metrics = await query_service.list_metrics(ctx.deps.org_id)

        # Return the list (service already returns the simplified format)
        return metrics

    @agent.tool
    async def create_metric_tool(ctx: RunContext[ChatDependencies], params: CreateMetricParams) -> dict:
        """Create a new metric definition.

        Use this when the user wants to define a new metric. The metric will be stored
        in Metricly and available for querying after manifest regeneration.

        Args:
            params: The metric configuration including name, type, description, and type_params.

        Returns:
            The created metric or an error message.
        """
        await emit_status(ctx.deps, "Creating new metric...")

        # Build metric document
        metric_doc = {
            "name": params.name,
            "description": params.description,
            "type": params.type,
            "type_params": params.type_params.model_dump(exclude_none=True),
        }
        if params.label:
            metric_doc["label"] = params.label

        try:
            user = _get_user_context(ctx.deps)
            result = await manifest_service.create_metric(user, metric_doc)
            return {"success": True, "metric": result}
        except ValueError as e:
            # Service raises ValueError for validation/already-exists errors
            return {"error": str(e)}
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    @agent.tool
    async def update_metric_tool(
        ctx: RunContext[ChatDependencies], metric_name: str, updates: UpdateMetricParams
    ) -> dict:
        """Update an existing metric's description, label, or type parameters.

        Use this when the user wants to modify an existing metric definition.
        Note: Only metrics created in Metricly can have their type changed.
        Imported metrics from dbt can only have description and label updated.

        Args:
            metric_name: The name of the metric to update.
            updates: The fields to update.

        Returns:
            The updated metric or an error message.
        """
        await emit_status(ctx.deps, "Updating metric definition...")

        # Build updates dict
        update_dict = updates.model_dump(exclude_none=True)
        if "type_params" in update_dict and updates.type_params:
            # Convert type_params to plain dict
            update_dict["type_params"] = updates.type_params.model_dump(exclude_none=True)

        if not update_dict:
            return {"error": "No updates provided."}

        try:
            user = _get_user_context(ctx.deps)
            result = await manifest_service.update_metric(user, metric_name, update_dict)
            return {"success": True, "metric": result}
        except ValueError as e:
            # Service raises ValueError for not-found errors
            return {"error": str(e)}
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    @agent.tool
    async def delete_metric_tool(ctx: RunContext[ChatDependencies], metric_name: str) -> dict:
        """Delete a metric definition.

        Use this when the user wants to remove a metric. Note that only metrics
        created in Metricly can be deleted. Imported metrics from dbt cannot be deleted
        (they will reappear on next import).

        Args:
            metric_name: The name of the metric to delete.

        Returns:
            Success status or an error message.
        """
        await emit_status(ctx.deps, "Deleting metric...")

        try:
            user = _get_user_context(ctx.deps)

            # Check if metric is imported (chat-specific warning)
            existing = storage.get_metric(ctx.deps.org_id, metric_name)
            is_imported = existing and existing.get("_origin") == "imported"

            # Use service for deletion (handles not-found and cache invalidation)
            await manifest_service.delete_metric(user, metric_name)

            # Return with warning for imported metrics
            if is_imported:
                return {
                    "warning": f"Metric '{metric_name}' was imported from dbt. "
                    "Deleting it will only remove it until the next manifest import.",
                    "deleted": True,
                }
            return {"success": True}
        except ValueError as e:
            # Service raises ValueError for not-found errors
            return {"error": str(e)}
        except PermissionError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}

    @agent.tool
    async def preview_metric_tool(
        ctx: RunContext[ChatDependencies], params: CreateMetricParams, grain: str | None = None
    ) -> dict:
        """Preview query results for a metric definition before saving.

        Use this to test a metric configuration and show the user what data it would return.
        This is useful before creating or updating a metric.

        Args:
            params: The metric configuration to preview.
            grain: Optional time grain (day, week, month).

        Returns:
            Sample query results or an error message.
        """
        await emit_status(ctx.deps, "Previewing metric configuration...")

        # Build metric document
        metric_doc = {
            "name": params.name,
            "description": params.description,
            "type": params.type,
            "type_params": params.type_params.model_dump(exclude_none=True),
        }
        if params.label:
            metric_doc["label"] = params.label

        # Build sample query params
        sample_query = {"grain": grain} if grain else None

        try:
            user = _get_user_context(ctx.deps)
            result = await manifest_service.preview_metric(user, metric_doc, sample_query)
            return result
        except Exception as e:
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # Context (User Preferences) Tools
    # -------------------------------------------------------------------------

    @agent.tool
    async def update_user_preferences_tool(
        ctx: RunContext[ChatDependencies],
        default_currency: str | None = None,
        default_grain: str | None = None,
        decimal_places: int | None = None,
        preferred_chart_type: str | None = None,
        custom_instructions: str | None = None,
    ) -> dict:
        """Save user preferences for future conversations.

        Use this when the user expresses a preference that should persist across sessions,
        such as "I prefer seeing revenue in EUR" or "Use monthly grain by default".

        Args:
            default_currency: Preferred currency code (e.g., "USD", "EUR", "GBP")
            default_grain: Preferred time granularity (e.g., "day", "week", "month")
            decimal_places: Number of decimal places for numeric values
            preferred_chart_type: Preferred chart type for visualizations
            custom_instructions: Any custom instructions the user wants you to follow

        Returns:
            Updated preferences or an error message.
        """
        await emit_status(ctx.deps, "Saving your preferences...")

        from services.context import update_user_preferences

        updates = {}
        if default_currency is not None:
            updates["default_currency"] = default_currency
        if default_grain is not None:
            updates["default_grain"] = default_grain
        if decimal_places is not None:
            updates["decimal_places"] = decimal_places
        if preferred_chart_type is not None:
            updates["preferred_chart_type"] = preferred_chart_type
        if custom_instructions is not None:
            updates["custom_instructions"] = custom_instructions

        if not updates:
            return {"error": "No preferences to update"}

        try:
            result = await update_user_preferences(ctx.deps.user_id, updates)
            return {
                "success": True,
                "message": "Preferences saved. I'll remember these for future conversations.",
                "preferences": result.model_dump(exclude_none=True),
            }
        except Exception as e:
            return {"error": str(e)}

    @agent.tool
    async def add_note_tool(ctx: RunContext[ChatDependencies], subject: str, note: str) -> dict:
        """Save a note about a metric, data source, or topic.

        Use this to record insights, caveats, or context that should be remembered
        for future conversations. For example:
        - "Revenue excludes refunds as of Q3 2024"
        - "Marketing spend data is delayed by 2 days"
        - "Q1 2024 data is unreliable due to migration"

        Args:
            subject: Subject of the note (e.g., metric name, data topic)
            note: The note content to remember

        Returns:
            Updated notes or an error message.
        """
        await emit_status(ctx.deps, "Saving note...")

        from services.context import add_note

        try:
            result = await add_note(ctx.deps.user_id, subject, note)
            return {
                "success": True,
                "message": f"Note saved. I'll remember this about '{subject}'.",
                "notes": result.notes,
            }
        except Exception as e:
            return {"error": str(e)}

    @agent.tool
    async def add_favorite_metric_tool(ctx: RunContext[ChatDependencies], metric_name: str) -> dict:
        """Add a metric to the user's favorites.

        Use this when the user indicates a metric is important to them or they
        frequently ask about it.

        Args:
            metric_name: Name of the metric to add to favorites

        Returns:
            Updated favorites list or an error message.
        """
        from services.context import add_favorite

        try:
            result = await add_favorite(ctx.deps.user_id, metric_name)
            return {
                "success": True,
                "message": f"Added '{metric_name}' to your favorites.",
                "favorite_metrics": result.favorite_metrics,
            }
        except Exception as e:
            return {"error": str(e)}

    @agent.instructions
    def dynamic_instructions(ctx: RunContext[ChatDependencies]) -> str:
        """Inject tenant-specific context into the system prompt."""
        from datetime import datetime

        # Current date/time context
        now = datetime.now()
        date_context = f"""## CURRENT DATE/TIME

Today is {now.strftime('%A, %B %d, %Y')} ({now.strftime('%Y-%m-%d')}).
Current time: {now.strftime('%H:%M')} (UTC).

Use this when interpreting relative time references like "this month", "last week", "yesterday", etc.

"""

        # User preferences context (accumulated memory)
        preferences_context = ""
        if ctx.deps.user_preferences:
            prefs = ctx.deps.user_preferences
            prefs_parts = []

            # Format preferences
            if prefs.get('default_currency'):
                prefs_parts.append(f"- Preferred currency: {prefs['default_currency']}")
            if prefs.get('default_grain'):
                prefs_parts.append(f"- Preferred time grain: {prefs['default_grain']}")
            if prefs.get('decimal_places') is not None:
                prefs_parts.append(f"- Decimal places: {prefs['decimal_places']}")
            if prefs.get('preferred_chart_type'):
                prefs_parts.append(f"- Preferred chart type: {prefs['preferred_chart_type']}")

            # Favorite metrics
            if prefs.get('favorite_metrics'):
                favorites = prefs['favorite_metrics']
                prefs_parts.append(f"- Favorite metrics: {', '.join(favorites)}")

            # Notes about data/metrics
            if prefs.get('notes'):
                notes = prefs['notes']
                notes_str = "\n".join(f"  - {subject}: {note}" for subject, note in notes.items())
                prefs_parts.append(f"- Notes:\n{notes_str}")

            # Custom instructions from user
            if prefs.get('custom_instructions'):
                prefs_parts.append(f"- Custom instructions: {prefs['custom_instructions']}")

            if prefs_parts:
                preferences_context = f"""## YOUR MEMORY (User Preferences)

This user has saved the following preferences. Use these to personalize responses:

{chr(10).join(prefs_parts)}

When you learn new user preferences during conversation (e.g., "I prefer seeing revenue in EUR"),
remember to suggest saving them for future sessions.

"""

        # Load prompts from generated schema documentation
        widget_prompt = _get_widget_prompt()
        base_prompt = date_context + preferences_context + SYSTEM_PROMPT.format(
            context=ctx.deps.tenant_context,
            widget_types=widget_prompt
        )

        # Add widget context if present
        if ctx.deps.widget_context:
            widget = ctx.deps.widget_context

            # Add dashboard controls context
            controls_info = ""
            if ctx.deps.widget_dashboard_controls:
                ctrl = ctx.deps.widget_dashboard_controls
                date_range = ctrl.get('date_range', {})
                controls_info = f"""
## DASHBOARD CONTROLS (Applied to this widget)

The dashboard currently filters data with these global controls:
- Date Range: {date_range.get('from', 'N/A')} to {date_range.get('to', 'N/A')}
- Grain: {ctrl.get('grain', 'N/A')}

IMPORTANT: Widgets inherit date filtering from dashboard controls automatically.
- Widget queries do NOT need start_date/end_date - the dashboard handles this
- The grain in the widget query controls time-series grouping, NOT date filtering
- KPI widgets typically don't need a grain - they show totals for the dashboard's date range
"""

            # Format rendered data for display
            rendered_data_info = ""
            if ctx.deps.widget_rendered_data:
                data = ctx.deps.widget_rendered_data
                # Show first few rows of data
                preview_rows = data[:10]  # Limit to first 10 rows
                if preview_rows:
                    import json
                    data_preview = json.dumps(preview_rows, indent=2, default=str)
                    rendered_data_info = f"""
## CURRENTLY DISPLAYED DATA

The widget is currently showing this data (first {len(preview_rows)} of {len(data)} rows):
```json
{data_preview}
```

This is what the user sees in the widget right now. Use this to understand the actual values being displayed.
"""

            # Format the widget format info
            format_info = widget.get('format')
            if format_info:
                format_str = f"- Format: type={format_info.get('type')}"
                if format_info.get('currency'):
                    format_str += f", currency={format_info.get('currency')}"
                if format_info.get('decimals') is not None:
                    format_str += f", decimals={format_info.get('decimals')}"
            else:
                format_str = "- Format: none (default)"

            # Load format prompt from generated schema documentation
            format_prompt = _get_format_prompt()

            widget_info = f"""
## CURRENT WIDGET (Edit Mode Active)

You are editing the following widget:
- Title: {widget.get('title', 'Untitled')}
- Type: {widget.get('type', 'unknown')}
- Metrics: {widget.get('query', {}).get('metrics', [])}
- Dimensions: {widget.get('query', {}).get('dimensions', [])}
- Grain: {widget.get('query', {}).get('grain', 'none')}
{format_str}
{controls_info}{rendered_data_info}
{format_prompt}

IMPORTANT: If changing from a currency metric to a percentage metric (or vice versa), you MUST update the format accordingly!

When the user asks to modify this widget, return a `widget_update` with the full updated configuration including the correct format.
"""
            return base_prompt + widget_info

        # Add full dashboard manipulation mode if full dashboard is provided
        if ctx.deps.full_dashboard:
            import json
            dashboard = ctx.deps.full_dashboard
            dashboard_prompt = _get_dashboard_prompt()
            format_prompt = _get_format_prompt()
            widget_prompt = _get_widget_prompt()

            # Create a summary of the dashboard structure
            pages_summary = []
            for page in dashboard.get('pages', []):
                widgets_count = sum(len(s.get('widgets', [])) for s in page.get('sections', []))
                sections_count = len(page.get('sections', []))
                pages_summary.append(f"- {page.get('title', 'Untitled')} ({sections_count} sections, {widgets_count} widgets)")

            dashboard_manipulation_info = f"""
## DASHBOARD MANIPULATION MODE (Full Edit)

You have access to the COMPLETE dashboard definition. When the user requests structural changes
(add/remove/reorder widgets, sections, or pages), return a `dashboard_update` with the modified
dashboard definition.

{dashboard_prompt}

{widget_prompt}

{format_prompt}

### Current Dashboard Summary
- Title: {dashboard.get('title', 'Untitled')}
- Pages: {len(dashboard.get('pages', []))}
{chr(10).join(pages_summary)}

### Full Dashboard Definition
```json
{json.dumps(dashboard, indent=2, default=str)}
```

### Response Guidelines

For STRUCTURAL changes (add/remove/move widgets, sections, pages):
- Return `dashboard_update` with the complete modified dashboard
- Preserve all IDs for existing elements
- Generate new UUIDs for new elements
- Keep metadata (id, owner, created_at, created_by, version) unchanged
- Update `updated_at` to current timestamp

For SIMPLE widget additions:
- You can still use `dashboard_action` with action="add_widget" for simple cases
- Use `dashboard_update` for complex operations or when modifying multiple elements

IMPORTANT: The frontend will show the user a diff and ask for confirmation before applying changes.
"""
            return base_prompt + dashboard_manipulation_info

        # Add dashboard context if present (legacy mode for simple add_widget)
        if ctx.deps.dashboard_context:
            pages_info = []
            for page in ctx.deps.dashboard_context.pages:
                sections_info = [
                    f"  - Section {i}: {s.title or 'Untitled'} ({s.widget_count} widgets)"
                    for i, s in enumerate(page.sections)
                ]
                pages_info.append(f"- Page '{page.title}' (id: {page.id}):\n" + "\n".join(sections_info))

            # Add controls info
            controls_info = ""
            if ctx.deps.dashboard_context.controls:
                ctrl = ctx.deps.dashboard_context.controls
                controls_info = f"""
## DASHBOARD CONTROLS (Global Filters)

The dashboard has global date controls that filter ALL widgets automatically:
- Current Date Range: {ctrl.date_range.get('from', 'N/A')} to {ctrl.date_range.get('to', 'N/A')}
- Current Grain: {ctrl.grain}

IMPORTANT: Widgets do NOT need their own date filters - they inherit from dashboard controls.
- Widget queries should NOT include start_date/end_date unless showing a DIFFERENT time period
- The grain in widget queries is for time-series charts (how to group time), NOT for filtering
- KPI widgets typically don't need a grain - they show the total for the selected date range
"""

            dashboard_info = f"""
## DASHBOARD STRUCTURE

Available pages and sections to add widgets to:
{chr(10).join(pages_info)}
{controls_info}
When the user asks to add a widget to the dashboard, return a `dashboard_action` with:
- action: "add_widget"
- page_id: the ID of the target page
- section_index: the index of the target section (0-based)
- widget: the widget configuration (type, title, query)
"""
            return base_prompt + dashboard_info

        return base_prompt


