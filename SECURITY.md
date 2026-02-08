# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in nanobot, please report it by:

1. **DO NOT** open a public GitHub issue
2. Create a private security advisory on GitHub or contact the repository maintainers
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We aim to respond to security reports within 48 hours.

---

## Security Protections

### Shell Injection Prevention
- Commands executed via `create_subprocess_exec()` with `shlex.split()` (no shell mode)
- Injection patterns blocked: `;`, `&&`, `||`, `|`, backticks, `$()`, `${}`, `<<`
- Deny patterns block destructive commands: `rm -rf`, `format`, `mkfs`, `dd`, `shutdown`, fork bombs
- Command length limited to 5000 characters

### SSRF (Server-Side Request Forgery) Protection
- All URLs validated before fetching with DNS resolution check
- Blocks internal/private IPs: localhost, 127.0.0.1, ::1, 169.254.169.254 (AWS metadata), private ranges
- Redirect following done manually with SSRF re-validation at each hop
- Maximum 5 redirects

### Path Traversal Prevention
- Secure path resolution via `Path.resolve()` + `relative_to()` (not string prefix matching)
- `..` components rejected before resolution
- Parent directories validated to be within allowed workspace
- File size limits: 10MB for reads and writes

### Access Control (Fail-Secure)
- Empty `allow_from` list **denies all** access (fail-secure default)
- Each sender must be explicitly added to the channel's `allowFrom` list
- `restrict_to_workspace` defaults to `True`

### Rate Limiting
- Token bucket algorithm per session, per operation
- Limits: messages (10/min), tool exec (5/min), web fetch (20/min), file writes (30/min), subagent spawns (3/5min), cron jobs (10/hour)
- Message size limit: 50KB per channel message, 100KB per session message

### Credential Protection
- API keys passed directly to LLM provider calls (not solely via environment variables)
- Error messages sanitized to remove API keys, tokens, passwords before returning to users
- Tool results sanitized before adding to LLM context
- Config files written atomically (tempfile + rename) with `chmod 600`
- Warning if config file is world-readable

### Resource Limits
- Session: max 1000 messages, 100 cached sessions (LRU eviction), 30-day expiry
- Context: max 500KB per bootstrap file, max 5MB per image, max 5 images per message
- Subagents: max 5 concurrent
- Message bus: bounded queues (1000 messages), 5s backpressure timeout
- Cron: max 50 jobs, minimum 60s interval

### Gateway Binding
- Default bind address is `127.0.0.1` (localhost only)
- Use a reverse proxy (nginx, caddy) for remote access

---

## Security Checklist for Deploy

1. Set `restrictToWorkspace: true` in config (default)
2. Add explicit `allowFrom` IDs for each enabled channel
3. Verify gateway binds to `127.0.0.1` (or use reverse proxy)
4. Run `nanobot security-check` to validate configuration
5. Ensure config file permissions: `chmod 600 ~/.nanobot/config.json`
6. Use environment variables or config for API keys (never hardcode)
7. Running as non-root user
8. Dependencies updated to latest secure versions

---

## Breaking Changes (v2.0 Security Hardening)

1. **`allowFrom` empty now denies all** — you must add user/phone IDs explicitly
2. **`restrictToWorkspace` now defaults to `True`** — set `false` in config if you need broader file access
3. **Gateway now binds to `127.0.0.1`** — use a reverse proxy for remote access, or set `host: "0.0.0.0"` explicitly

### Migration Guide

```json
{
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "YOUR_BOT_TOKEN",
      "allowFrom": ["123456789"]
    }
  },
  "tools": {
    "restrictToWorkspace": false
  },
  "gateway": {
    "host": "0.0.0.0"
  }
}
```

---

## Running Security Tests

```bash
pytest tests/security/ -v
```

## Verifying Configuration

```bash
nanobot security-check
```

## Manually Testing Protections

```bash
# Shell injection should be blocked
nanobot agent -m "exec command='ls; rm -rf /'"

# SSRF should be blocked
nanobot agent -m "web_fetch url='http://127.0.0.1'"

# Path traversal should be blocked
nanobot agent -m "read_file path='../../../etc/passwd'"
```

---

## Security Best Practices

### API Key Management

**CRITICAL**: Never commit API keys to version control.

```bash
# Store in config file with restricted permissions
chmod 600 ~/.nanobot/config.json
```

### Production Deployment

1. **Isolate the Environment** - Run in a container or VM
2. **Use a Dedicated User** - `sudo -u nanobot nanobot gateway`
3. **Set Proper Permissions** - `chmod 700 ~/.nanobot`
4. **Monitor Logs** - Watch for unauthorized access attempts
5. **Regular Updates** - `pip install --upgrade nanobot-ai`

### Data Privacy

- Logs may contain sensitive information — secure log files appropriately
- LLM providers see your prompts — review their privacy policies
- Chat history is stored locally — protect the `~/.nanobot` directory

---

**Last Updated**: 2026-02-08
