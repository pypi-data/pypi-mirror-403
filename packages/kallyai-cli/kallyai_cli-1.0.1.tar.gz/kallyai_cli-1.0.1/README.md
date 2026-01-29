# KallyAI CLI

A command-line interface for [KallyAI](https://kallyai.com) - an AI phone assistant that makes calls to businesses on your behalf.

## Features

- **Make AI phone calls** - Reserve tables, schedule appointments, inquire about services
- **Check usage** - Monitor your minutes and calls remaining
- **View call history** - List and inspect past calls
- **Get transcripts** - Read full conversation transcripts
- **Manage billing** - Access Stripe billing portal

## Installation

```bash
pip install kallyai-cli
```

Or install from source:

```bash
git clone https://github.com/sltelitsyn/kallyai-cli.git
cd kallyai-cli
pip install -e .
```

## Quick Start

```bash
# Check your usage (will prompt for login on first use)
kallyai --usage

# Make a call
kallyai --phone "+15551234567" --task "Ask about store hours"

# View call history
kallyai --history
```

## Authentication

Authentication is automatic. On first use, a browser window opens for Google/Apple sign-in. Tokens are securely stored locally.

```bash
kallyai --login      # Force re-authentication
kallyai --logout     # Clear saved credentials
kallyai --auth-status # Check if logged in
```

## Commands

### Making Calls

```bash
kallyai -p "+15551234567" -t "Reserve a table for 4 at 8pm" \
  --category restaurant \
  --name "John Smith" \
  --party-size 4 \
  --date "2026-01-28" \
  --time "20:00"
```

| Option | Short | Description |
|--------|-------|-------------|
| `--phone` | `-p` | Phone number (E.164 format) |
| `--task` | `-t` | What the AI should accomplish |
| `--category` | `-c` | restaurant, clinic, hotel, general |
| `--language` | `-l` | en or es |
| `--name` | | Your name (for reservations) |
| `--business` | | Business name |
| `--party-size` | | Party size (restaurants) |
| `--date` | | YYYY-MM-DD |
| `--time` | | HH:MM (24-hour) |

### Account & Usage

```bash
kallyai --usage        # Show minutes/calls remaining
kallyai --subscription # Show subscription status
kallyai --billing      # Open Stripe billing portal
```

### Call History

```bash
kallyai --history              # List recent calls
kallyai --call-info <ID>       # Get call details
kallyai --transcript <ID>      # Get conversation transcript
```

## Claude Code Skill Installation

This CLI can be used as a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) skill, allowing Claude to make phone calls on your behalf.

### Method 1: One-Line Install (Recommended)

```bash
# Install CLI globally
pip install kallyai-cli

# Create skills directory and download skill file
mkdir -p ~/.claude/skills/kallyai-api
curl -o ~/.claude/skills/kallyai-api/SKILL.md \
  https://raw.githubusercontent.com/sltelitsyn/kallyai-cli/main/skill/SKILL.md
```

### Method 2: Install from Source

```bash
# Clone repository
git clone https://github.com/sltelitsyn/kallyai-cli.git
cd kallyai-cli

# Install CLI
pip install -e .

# Copy skill to Claude Code
mkdir -p ~/.claude/skills/kallyai-api
cp skill/SKILL.md ~/.claude/skills/kallyai-api/
```

### Method 3: User Settings (Alternative)

Add to your Claude Code settings file (`~/.claude/settings.json`):

```json
{
  "skills": {
    "kallyai-api": {
      "path": "/path/to/kallyai-cli/skill"
    }
  }
}
```

### Usage in Claude Code

Once installed, Claude will automatically use the skill when you mention:
- "call", "phone call", "make a call"
- "reservation", "book a table"
- "appointment", "schedule"
- "KallyAI"

**Example prompts:**
- "Call +15551234567 and ask about their store hours"
- "Make a reservation at Italian Bistro for 4 people at 8pm"
- "Check my KallyAI usage"
- "Show my recent calls"

## Security

- **Token storage**: `~/.kallyai_token.json` with 0600 permissions
- **CSRF protection**: State parameter validation
- **Localhost only**: OAuth redirects only to localhost/127.0.0.1
- **Auto-refresh**: Tokens refresh automatically when expired

## API Documentation

For direct API usage, see the [API Reference](docs/api-reference.md).

## Requirements

- Python 3.10+
- httpx

## License

Proprietary License - see [LICENSE](LICENSE)

This software is provided under a proprietary license. You may use it solely
for personal or internal business purposes in connection with KallyAI services.
Reverse engineering, decompilation, and security testing are prohibited without
prior written consent.

## Links

- [KallyAI Website](https://kallyai.com)
- [Pricing](https://kallyai.com/pricing)
- [API Documentation](https://api.kallyai.com/docs)
