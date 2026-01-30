# Metricly CLI

Query metrics and manage dashboards from the terminal.

## Installation

### Using uv (Recommended)

```bash
# Install from local build
uv tool install ./backend

# Or install from GitHub (once published)
uv tool install git+https://github.com/metricly/metricly#subdirectory=backend
```

### Using pip

```bash
pip install ./backend
```

## Quick Start

```bash
# Login with Google OAuth
metricly login

# Check who you're logged in as
metricly whoami

# List available metrics
metricly metrics list

# Query metrics
metricly query -m total_revenue -g month --limit 5

# Get visualization suggestions
metricly query -m total_revenue -g month --suggest-viz

# Export to JSON
metricly query -m total_revenue --format json > data.json
```

## Commands

### Authentication

```bash
metricly login          # Login via Google OAuth (opens browser)
metricly whoami         # Show current user and organization
metricly logout         # Clear stored credentials
metricly org list       # List your organizations
metricly org switch ID  # Switch to a different organization
```

### Querying Metrics

```bash
# List available metrics
metricly metrics list
metricly metrics list --format json

# Get metric details
metricly metrics show total_revenue

# Query data
metricly query -m revenue -g month                    # Monthly revenue
metricly query -m revenue -d region --limit 10        # By region
metricly query -m revenue -m orders -g week           # Multiple metrics
metricly query -m revenue --start 2024-01-01 --end 2024-12-31

# With visualization suggestion
metricly query -m revenue -g month --suggest-viz

# List dimensions
metricly dimensions list
```

### Dashboard Management

```bash
# List dashboards
metricly dashboards list

# Show dashboard details
metricly dashboards show DASHBOARD_ID

# Create a new dashboard
metricly dashboards create "My Dashboard"
metricly dashboards create "Team Metrics" -v org  # Visible to team

# Delete a dashboard
metricly dashboards delete DASHBOARD_ID
metricly dashboards delete DASHBOARD_ID --yes     # Skip confirmation
```

### Manifest Management (Admin Only)

```bash
# View manifest status
metricly manifest status

# Export manifest
metricly manifest export -o manifest.yaml

# Import manifest
metricly manifest upload manifest.yaml
metricly manifest upload manifest.yaml --force  # Overwrite conflicts

# Semantic models
metricly models list
metricly models show orders
metricly models create model.yaml
metricly models update orders updated.yaml
metricly models delete orders

# Metrics
metricly metrics create metric.yaml
metricly metrics update total_revenue updated.yaml
metricly metrics delete total_revenue
metricly metrics preview metric.yaml  # Test before saving
```

## Output Formats

All commands support `--format`:

| Format | Description |
|--------|-------------|
| `table` | Human-readable ASCII table (default) |
| `json` | JSON output for scripting |
| `yaml` | YAML output for config editing |

```bash
metricly metrics list --format json | jq '.[0]'
metricly dashboards show abc123 --format yaml > dashboard.yaml
```

## Configuration

Credentials are stored in `~/.metricly/`:

```
~/.metricly/
├── credentials.json    # OAuth tokens (encrypted)
└── config.json         # User preferences
```

## Development

```bash
# Build the wheel
cd backend
uv build

# Install locally for testing
uv tool install dist/metricly_cli-*.whl --force

# Run tests
uv run pytest tests/ -v
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `FIRESTORE_EMULATOR_HOST` | Use Firestore emulator |
| `FIREBASE_AUTH_EMULATOR_HOST` | Use Auth emulator |
| `ENV` | Environment: `production`, `development`, `test` |
