---
name: kallyai-api
description: Make phone calls via KallyAI API - an AI phone assistant that calls businesses on your behalf. Use when users want to make restaurant reservations, schedule appointments, or inquire at businesses by phone. Triggers on "call", "phone", "reservation", "appointment", "KallyAI".
---

# KallyAI API Integration

KallyAI is an AI phone assistant that makes calls to businesses on behalf of users.

## Quick Start

```bash
# Check usage (auto-authenticates if needed)
kallyai --usage

# Make a call
kallyai -p "+15551234567" -t "Ask about store hours"

# View call history
kallyai --history
```

## Complete Workflow

### Step 1: Gather Call Details

Collect from user:
- **Phone number** to call (required)
- **What to accomplish** - the task description (required)
- **Category**: restaurant, clinic, hotel, or general (required)
- For reservations: name, date, time, party size

### Step 2: Authenticate User

Authentication is automatic. First API call opens browser for Google/Apple sign-in.

For manual control:
```bash
kallyai --login     # Force re-auth
kallyai --logout    # Clear credentials
kallyai --auth-status  # Check login
```

### Step 3: Make the Call

```bash
kallyai \
  --phone "+15551234567" \
  --task "Reserve table for 4 at 8pm" \
  --category restaurant \
  --name "John Smith" \
  --party-size 4 \
  --date "2026-01-28" \
  --time "20:00"
```

### Step 4: Check Results

```bash
# List recent calls
kallyai --history

# Get call details
kallyai --call-info <CALL_ID>

# Get transcript
kallyai --transcript <CALL_ID>
```

---

## CLI Commands Reference

### Making Calls

| Option | Short | Description |
|--------|-------|-------------|
| `--phone` | `-p` | Phone number (E.164: +15551234567) |
| `--task` | `-t` | What AI should accomplish |
| `--category` | `-c` | restaurant, clinic, hotel, general |
| `--language` | `-l` | en or es |
| `--name` | | Your name (for reservations) |
| `--business` | | Business name |
| `--party-size` | | Party size (restaurants) |
| `--date` | | YYYY-MM-DD |
| `--time` | | HH:MM (24-hour) |

### Account & Usage

| Command | Description |
|---------|-------------|
| `--usage` | Show minutes/calls remaining |
| `--subscription` | Show subscription status |
| `--billing` | Open Stripe billing portal |
| `--history` | List recent calls |
| `--call-info ID` | Get call details |
| `--transcript ID` | Get call transcript |

### Authentication

| Command | Description |
|---------|-------------|
| `--login` | Force re-authentication |
| `--logout` | Clear saved credentials |
| `--auth-status` | Check if logged in |

---

## API Direct Usage

For programmatic access, use the REST API directly:

### Authentication

For CLI/terminal tools:
```
https://api.kallyai.com/v1/auth/cli?redirect_uri=http://localhost:PORT
```

After sign-in, redirects to:
```
http://localhost:PORT?access_token=...&refresh_token=...&expires_in=3600
```

### Make a Call

```
POST https://api.kallyai.com/v1/calls
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "submission": {
    "task_category": "general",
    "task_description": "Ask about store hours",
    "respondent_phone": "+15551234567",
    "language": "en",
    "call_language": "en"
  },
  "timezone": "America/New_York"
}
```

### Check Usage

```
GET https://api.kallyai.com/v1/users/me/statistics
Authorization: Bearer <access_token>
```

Response:
```json
{
  "minutes_allocated": 210,
  "minutes_used": 45,
  "minutes_remaining": 165,
  "calls_remaining": 27
}
```

### Check Subscription

```
GET https://api.kallyai.com/v1/users/me/subscription
Authorization: Bearer <access_token>
```

### List Calls

```
GET https://api.kallyai.com/v1/calls?limit=10
Authorization: Bearer <access_token>
```

### Get Call Details

```
GET https://api.kallyai.com/v1/calls/{call_id}
Authorization: Bearer <access_token>
```

### Get Transcript

```
GET https://api.kallyai.com/v1/calls/{call_id}/transcript
Authorization: Bearer <access_token>
```

---

## Security

**Token Storage:**
- Tokens are stored in `~/.kallyai_token.json` with 0600 permissions (owner read/write only)
- Never commit token files to version control

**CLI Auth Flow Security:**
- Only `localhost` and `127.0.0.1` redirect URIs are accepted
- CSRF protection via `state` parameter
- Dynamic port selection (prevents port hijacking)
- Tokens expire after 1 hour, auto-refresh supported

**Best Practices:**
- Use `--logout` to clear tokens when done
- Don't share tokens or pass them in command-line args in shared environments

---

## Common Errors

| Code | HTTP | Action |
|------|------|--------|
| `quota_exceeded` | 402 | User needs to upgrade at kallyai.com/pricing |
| `missing_phone_number` | 422 | Ask user for phone number |
| `emergency_number` | 422 | Cannot call 911/emergency services |
| `country_restriction` | 403 | Country not supported |

## Full API Reference

See [docs/api-reference.md](../docs/api-reference.md) for complete schema documentation.
