# Authentication

Authenticate with Azure Entra for API access.

## Commands

| Command | Description |
|---------|-------------|
| `dxs auth login` | Authenticate with Azure Entra |
| `dxs auth logout` | Clear stored credentials |
| `dxs auth status` | Show current auth status |

## Login

```bash
uv run dxs auth login
```

This initiates device code flow:
1. Opens browser or displays a URL
2. Enter the code shown
3. Complete Azure login
4. Tokens stored in `~/.datex/credentials.yaml`

### Example Output

```yaml
authentication:
  message: Authentication successful
  user: user@datexcorp.com
  expires: '2026-01-15T10:30:00Z'
metadata:
  success: true
```

## Check Status

```bash
uv run dxs auth status
```

### Example Output

```yaml
authentication:
  authenticated: true
  user: user@datexcorp.com
  expires_in: 3542 seconds
  resources:
    datex_api:
      status: valid
      expires: '2026-01-14T20:30:00Z'
    azure_devops:
      status: valid
      expires: '2026-01-14T20:30:00Z'
    dynamics_crm:
      status: not_configured
metadata:
  success: true
```

## Logout

```bash
uv run dxs auth logout
```

Clears all stored credentials.

## Token Storage

Credentials are stored in:
```
~/.datex/credentials.yaml
```

## Troubleshooting

### Token Expired
```bash
# Re-authenticate
uv run dxs auth login
```

### Permission Denied
- Verify you have access to the resources
- Check with your admin for permissions

### DevOps Not Working
- Ensure Azure DevOps consent was granted during login
- May need to re-login to grant additional permissions

## See Also

- [Configuration](./configuration.md) - Set default org/repo
- [DevOps Integration](../devops-integration/) - Work item queries
