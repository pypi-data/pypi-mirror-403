# mushu-cli

Command-line interface for the Mushu platform.

## Features

- **Authentication**: Sign in with Apple via web OAuth
- **Organization Management**: Create and manage organizations
- **Notification Tenants**: Configure APNs credentials and send push notifications
- **Payment**: Manage Stripe integration and org wallet
- **Media**: Upload and manage images/videos
- **Device Management**: Register and list device tokens
- **Per-Project Config**: Local `.mushu.json` for project-specific settings

## Installation

```bash
pip install mushu-cli
```

Or install from source:

```bash
cd mushu-cli
pip install -e .
```

## Quick Start

```bash
# Sign in
mushu auth login

# Create an organization
mushu org create "My Company"

# Initialize project config (creates .mushu.json)
mushu init --org org_abc123

# Commands now use that org automatically
mushu tenant create --bundle-id com.myapp.ios
mushu push send --user <user_id> --title "Hello" --body "World"
mushu media upload photo.jpg
```

## Project Configuration

### Per-Project Config (.mushu.json)

Create a `.mushu.json` file in your project root to set defaults for that project:

```bash
# Initialize with your org
mushu init --org org_abc123

# Or with more options
mushu init --org org_abc123 --tenant tenant_xyz --app app_def456
```

This creates a `.mushu.json` file:

```json
{
  "org_id": "org_abc123",
  "tenant_id": "tenant_xyz",
  "app_id": "app_def456"
}
```

The CLI automatically finds and uses this config when running commands from that directory (or any subdirectory).

### Config Resolution Order

Settings are resolved in this order (highest priority first):

1. **Command-line flags** (`--org`, `--tenant`, etc.)
2. **Environment variables** (`MUSHU_ORG_ID`, `MUSHU_TENANT_ID`, etc.)
3. **Local `.mushu.json`** (walked up from current directory)
4. **Global `~/.mushu/config.json`** defaults

### View Current Config

```bash
# Show status including which config is active
mushu status

# Show detailed config info
mushu config --show
```

## Commands

### Project Init

```bash
mushu init                              # Use current global defaults
mushu init --org <id>                   # Set org for this project
mushu init --org <id> --tenant <id>     # Set org and tenant
mushu init --force                      # Overwrite existing .mushu.json
```

### Authentication

```bash
mushu auth login              # Sign in with Apple
mushu auth logout             # Sign out
mushu auth whoami             # Show current user
```

### Organizations

```bash
mushu org create <name>       # Create organization
mushu org list                # List your organizations
mushu org show <id>           # Show organization details
mushu org delete <id>         # Delete organization
mushu org use <id>            # Set as global default
```

### Notification Tenants

```bash
mushu tenant create --bundle-id <bundle>  # Create tenant (uses project org)
mushu tenant list                          # List tenants
mushu tenant show <id>                     # Show tenant
mushu tenant delete <id>                   # Delete tenant
mushu tenant use <id>                      # Set as default tenant
```

### Push Notifications

```bash
mushu push send --user <id> --title "Title" --body "Body"
mushu push send --user <id> --silent --data '{"key":"value"}'
```

### Devices

```bash
mushu device register <token> --user <id> --platform ios
mushu device list
mushu device delete <id>
```

### Media

```bash
mushu media upload <file>     # Upload (uses project org)
mushu media list              # List media
mushu media show <id>
mushu media delete <id>
```

### Pay

```bash
mushu pay tenant create --name "My App"
mushu pay tenant list
mushu pay product create --name "Starter Pack" --price 999 --amount 10000000
```

### Global Configuration

```bash
mushu config --show                    # Show current config
mushu config --auth-url <url>          # Set auth API URL
mushu config --notify-url <url>        # Set notify API URL
mushu status                           # Show connection status
```

## Configuration Files

### Global (~/.mushu/)

- `config.json` - API URLs and global defaults
- `tokens.json` - Authentication tokens (created after login)

### Local (.mushu.json)

Project-specific settings. Supports:

| Field | Description |
|-------|-------------|
| `org_id` | Organization ID |
| `org_name` | Organization name (display only) |
| `app_id` | App ID |
| `app_name` | App name (display only) |
| `tenant_id` | Notification tenant ID |
| `pay_tenant_id` | Pay tenant ID |

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MUSHU_AUTH_URL` | Override auth API URL |
| `MUSHU_NOTIFY_URL` | Override notify API URL |
| `MUSHU_PAY_URL` | Override pay API URL |
| `MUSHU_MEDIA_URL` | Override media API URL |
| `MUSHU_ORG_ID` | Override org ID |
| `MUSHU_APP_ID` | Override app ID |
| `MUSHU_TENANT_ID` | Override tenant ID |
| `MUSHU_PAY_TENANT_ID` | Override pay tenant ID |
