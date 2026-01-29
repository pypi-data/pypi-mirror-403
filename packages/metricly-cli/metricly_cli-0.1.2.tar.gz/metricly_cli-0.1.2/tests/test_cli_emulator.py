"""Test CLI commands against Firebase emulators.

This test script bypasses OAuth authentication and directly tests
the CLI commands using a mock user context that matches the seeded data.
"""

import asyncio
import os
import sys
from unittest.mock import patch, MagicMock

# Set emulator environment before imports
os.environ["FIREBASE_AUTH_EMULATOR_HOST"] = "localhost:9099"
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8081"
os.environ["ENV"] = "test"

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typer.testing import CliRunner
from services.auth import UserContext


# Mock user matching the seeded demo user
MOCK_USER = UserContext(
    uid="test-cli-user",
    email="demo@metricly.xyz",
    org_id="local-dev",
    role="owner",
)


def create_mock_auth():
    """Create a mock auth manager that returns the test user."""
    mock_auth = MagicMock()
    mock_auth.is_logged_in.return_value = True
    mock_auth.get_stored_email.return_value = MOCK_USER.email

    async def mock_get_user():
        return MOCK_USER

    # Create a coroutine-like mock
    future = asyncio.Future()
    future.set_result(MOCK_USER)
    mock_auth.get_user.return_value = future
    return mock_auth


def run_cli_tests():
    """Run CLI command tests against emulators."""
    from cli.main import app

    runner = CliRunner()

    # Patch the auth manager
    mock_auth = create_mock_auth()

    print("\n" + "=" * 60)
    print("Testing CLI commands against Firebase emulators")
    print("=" * 60)

    with patch("cli.main.auth", mock_auth):
        with patch("cli.main.require_auth", return_value=MOCK_USER):
            # Test 1: version
            print("\n[1] metricly version")
            result = runner.invoke(app, ["version"])
            print(f"    Exit code: {result.exit_code}")
            print(f"    Output: {result.output.strip()}")

            # Test 2: whoami
            print("\n[2] metricly whoami")
            result = runner.invoke(app, ["whoami"])
            print(f"    Exit code: {result.exit_code}")
            print(f"    Output: {result.output.strip()[:200]}")

            # Test 3: metrics list
            print("\n[3] metricly metrics list")
            result = runner.invoke(app, ["metrics", "list"])
            print(f"    Exit code: {result.exit_code}")
            if result.exit_code == 0:
                lines = result.output.strip().split("\n")
                print(f"    Output ({len(lines)} lines):")
                for line in lines[:8]:
                    print(f"      {line}")
                if len(lines) > 8:
                    print(f"      ... and {len(lines) - 8} more lines")
            else:
                print(f"    Error: {result.output}")

            # Test 4: metrics list --format json
            print("\n[4] metricly metrics list --format json")
            result = runner.invoke(app, ["metrics", "list", "--format", "json"])
            print(f"    Exit code: {result.exit_code}")
            if result.exit_code == 0:
                import json
                try:
                    data = json.loads(result.output)
                    print(f"    Found {len(data)} metrics")
                    if data:
                        print(f"    First metric: {data[0].get('name', 'unknown')}")
                except json.JSONDecodeError:
                    print(f"    Invalid JSON output")
            else:
                print(f"    Error: {result.output}")

            # Test 5: dimensions list
            print("\n[5] metricly dimensions list")
            result = runner.invoke(app, ["dimensions", "list"])
            print(f"    Exit code: {result.exit_code}")
            if result.exit_code == 0:
                lines = result.output.strip().split("\n")
                print(f"    Found {len(lines) - 3} dimensions")  # Subtract header lines
            else:
                print(f"    Error: {result.output}")

            # Test 6: manifest status
            print("\n[6] metricly manifest status")
            result = runner.invoke(app, ["manifest", "status"])
            print(f"    Exit code: {result.exit_code}")
            print(f"    Output: {result.output.strip()[:300]}")

            # Test 7: models list
            print("\n[7] metricly models list")
            result = runner.invoke(app, ["models", "list"])
            print(f"    Exit code: {result.exit_code}")
            if result.exit_code == 0:
                lines = result.output.strip().split("\n")
                print(f"    Output ({len(lines)} lines):")
                for line in lines[:8]:
                    print(f"      {line}")
                if len(lines) > 8:
                    print(f"      ... and {len(lines) - 8} more lines")
            else:
                print(f"    Error: {result.output}")

            # Test 8: dashboards list
            print("\n[8] metricly dashboards list")
            result = runner.invoke(app, ["dashboards", "list"])
            print(f"    Exit code: {result.exit_code}")
            print(f"    Output: {result.output.strip()[:300]}")

            # Test 9: query command
            print("\n[9] metricly query -m total_revenue -g month --limit 5")
            result = runner.invoke(app, ["query", "-m", "total_revenue", "-g", "month", "--limit", "5"])
            print(f"    Exit code: {result.exit_code}")
            if result.exit_code == 0:
                print(f"    Output: {result.output.strip()[:400]}")
            else:
                print(f"    Error: {result.output[:400]}")

            # Test 10: query with visualization suggestion
            print("\n[10] metricly query -m total_revenue -g month --suggest-viz")
            result = runner.invoke(app, ["query", "-m", "total_revenue", "-g", "month", "--limit", "5", "--suggest-viz"])
            print(f"    Exit code: {result.exit_code}")
            if result.exit_code == 0:
                output = result.output.strip()
                if "Suggested" in output or "suggest" in output.lower():
                    print(f"    Visualization suggestion included!")
                print(f"    Output: {output[:500]}")
            else:
                print(f"    Error: {result.output[:400]}")

            # Test 11: dashboards create (test write operation)
            print("\n[11] metricly dashboards create 'CLI Test Dashboard'")
            result = runner.invoke(app, ["dashboards", "create", "CLI Test Dashboard"])
            print(f"    Exit code: {result.exit_code}")
            print(f"    Output: {result.output.strip()[:300]}")

            # Test 12: metrics show (specific metric details)
            print("\n[12] metricly metrics show total_revenue")
            result = runner.invoke(app, ["metrics", "show", "total_revenue"])
            print(f"    Exit code: {result.exit_code}")
            print(f"    Output: {result.output.strip()[:400]}")

    print("\n" + "=" * 60)
    print("CLI emulator tests complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_cli_tests()
