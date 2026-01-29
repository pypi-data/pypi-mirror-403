#!/usr/bin/env python3
"""
KallyAI CLI - Complete phone call management from the terminal.

Features:
- Make AI phone calls to businesses
- Check subscription and usage
- View call history and transcripts
- Manage billing

Usage:
    kallyai --phone "+15551234567" --task "Ask about hours"
    kallyai --usage          # Check minutes remaining
    kallyai --history        # List recent calls
    kallyai --call-info ID   # Get call details
"""

import argparse
import http.server
import json
import secrets
import socketserver
import sys
import threading
import time
import urllib.parse
import webbrowser
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Error: httpx is required. Install with: pip install httpx")
    sys.exit(1)

__version__ = "1.0.2"

# Configuration
API_BASE = "https://api.kallyai.com"
TOKEN_FILE = Path.home() / ".kallyai_token.json"
CALLBACK_PORT_RANGE = (8740, 8760)

# Global for OAuth callback
auth_result = {"access_token": None, "refresh_token": None, "error": None, "state": None}


# =============================================================================
# Token Management
# =============================================================================

def load_token() -> str | None:
    """Load saved token if valid, refresh if expired."""
    if TOKEN_FILE.exists():
        try:
            data = json.loads(TOKEN_FILE.read_text())
            if data.get("expires_at", 0) > time.time():
                return data.get("access_token")
            if data.get("refresh_token"):
                return _refresh_token(data["refresh_token"])
        except Exception:
            pass
    return None


def save_token(access_token: str, refresh_token: str = None, expires_in: int = 3600):
    """Save token securely (0600 permissions)."""
    TOKEN_FILE.write_text(json.dumps({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "expires_at": time.time() + expires_in - 60,
    }))
    TOKEN_FILE.chmod(0o600)


def _refresh_token(refresh_tok: str) -> str | None:
    """Refresh an expired access token."""
    with httpx.Client() as client:
        resp = client.post(
            f"{API_BASE}/v1/auth/refresh",
            json={"refresh_token": refresh_tok},
            headers={"User-Agent": f"KallyAI-CLI/{__version__}"},
        )
        if resp.status_code == 200:
            data = resp.json()
            save_token(data["access_token"], data.get("refresh_token"), data.get("expires_in", 3600))
            return data["access_token"]
    return None


# =============================================================================
# OAuth Authentication
# =============================================================================

class CallbackHandler(http.server.SimpleHTTPRequestHandler):
    """Handle OAuth callback with tokens in URL."""

    def do_GET(self):
        global auth_result
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "access_token" in params:
            auth_result["access_token"] = params["access_token"][0]
            auth_result["refresh_token"] = params.get("refresh_token", [None])[0]
            auth_result["state"] = params.get("state", [None])[0]
            self._send_html("Authentication Successful!", "#00d4ff",
                           "You can close this window and return to your terminal.")
        elif "error" in params:
            import html
            auth_result["error"] = params["error"][0]
            safe_error = html.escape(auth_result["error"])
            self._send_html("Authentication Failed", "#f87171", safe_error)
        else:
            self.send_response(404)
            self.end_headers()

    def _send_html(self, title: str, color: str, message: str):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(f'''<!DOCTYPE html>
<html><head><title>KallyAI - {title}</title></head>
<body style="font-family:system-ui;text-align:center;padding:50px;background:#06080d;color:#e6edf3;">
<h2 style="color:{color};">{title}</h2><p>{message}</p>
<script>setTimeout(() => window.close(), 2000);</script>
</body></html>'''.encode())

    def log_message(self, format, *args):
        pass


def authenticate() -> str:
    """OAuth authentication via browser with CSRF protection."""
    global auth_result
    auth_result = {"access_token": None, "refresh_token": None, "error": None, "state": None}

    csrf_state = secrets.token_urlsafe(32)

    # Find available port
    server = None
    callback_port = None
    for port in range(CALLBACK_PORT_RANGE[0], CALLBACK_PORT_RANGE[1]):
        try:
            server = socketserver.TCPServer(("127.0.0.1", port), CallbackHandler)
            callback_port = port
            break
        except OSError:
            continue

    if server is None:
        raise RuntimeError(f"No available port in range {CALLBACK_PORT_RANGE}")

    server_thread = threading.Thread(target=lambda: server.serve_forever())
    server_thread.daemon = True
    server_thread.start()

    callback_url = f"http://127.0.0.1:{callback_port}"
    auth_url = f"{API_BASE}/v1/auth/cli?redirect_uri={urllib.parse.quote(callback_url)}&state={csrf_state}"

    print("\n[key] Opening browser for sign-in...")
    print("   Sign in with your Google or Apple account.\n")
    webbrowser.open(auth_url)

    # Wait for callback
    timeout = 180
    start = time.time()
    while auth_result["access_token"] is None and auth_result["error"] is None:
        if time.time() - start > timeout:
            server.shutdown()
            raise TimeoutError("Authentication timed out")
        time.sleep(0.5)

    server.shutdown()

    if auth_result["error"]:
        raise Exception(f"Authentication failed: {auth_result['error']}")

    if auth_result.get("state") != csrf_state:
        raise Exception("CSRF state mismatch (possible attack)")

    save_token(auth_result["access_token"], auth_result["refresh_token"], 3600)
    print("[ok] Authentication successful!")
    return auth_result["access_token"]


def require_token() -> str:
    """Get token, authenticating if needed."""
    token = load_token()
    if not token:
        token = authenticate()
    return token


# =============================================================================
# API Client
# =============================================================================

def api_request(method: str, endpoint: str, token: str, **kwargs) -> dict:
    """Make authenticated API request."""
    with httpx.Client(timeout=300.0) as client:
        resp = client.request(
            method,
            f"{API_BASE}{endpoint}",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": f"KallyAI-CLI/{__version__}",
            },
            **kwargs
        )

    if resp.status_code == 401:
        TOKEN_FILE.unlink(missing_ok=True)
        raise Exception("Token expired. Please run again to re-authenticate.")

    if resp.status_code >= 400:
        try:
            err = resp.json().get("error", {})
            code = err.get("code", "unknown")
            msg = err.get("message") or err.get("details", {}).get("message", resp.text)
            raise Exception(f"{code}: {msg}")
        except json.JSONDecodeError:
            raise Exception(f"HTTP {resp.status_code}: {resp.text}")

    return resp.json() if resp.text else {}


# =============================================================================
# Commands
# =============================================================================

def cmd_subscription(token: str):
    """Show subscription status."""
    data = api_request("GET", "/v1/users/me/subscription", token)

    print("\n[info] Subscription Status")
    print("=" * 40)

    if data.get("has_active_subscription"):
        plan = data.get("plan", {})
        print(f"   Status: [ok] Active")
        print(f"   Plan: {plan.get('type', 'unknown').title()} ({plan.get('period', 'monthly')})")
        print(f"   Minutes: {plan.get('minutes_included', 0)} included")
        print(f"   Expires: {data.get('expires_at', 'N/A')}")
        print(f"   Auto-renew: {'Yes' if data.get('auto_renew') else 'No'}")
    else:
        print(f"   Status: [x] No active subscription")
        print(f"\n   Subscribe at: https://kallyai.com/pricing")

    print("=" * 40)


def cmd_usage(token: str):
    """Show usage statistics."""
    data = api_request("GET", "/v1/users/me/statistics", token)

    print("\n[chart] Usage Statistics")
    print("=" * 40)
    print(f"   Plan: {data.get('plan_type', 'unknown').title()}")
    print(f"   Status: {data.get('subscription_status', 'unknown')}")
    print()
    print(f"   Minutes: {data.get('minutes_used', 0):.1f} / {data.get('minutes_allocated', 0)}")
    print(f"   Remaining: {data.get('minutes_remaining', 0):.1f} minutes")
    print()
    print(f"   Calls: {data.get('calls_used', 0)} / {data.get('calls_allocated', 0)}")
    print(f"   Remaining: {data.get('calls_remaining', 0)} calls")
    print()
    pct = data.get('usage_percentage', 0)
    bar_filled = int(pct / 5)
    bar = "#" * bar_filled + "-" * (20 - bar_filled)
    print(f"   Usage: [{bar}] {pct:.1f}%")
    print()
    print(f"   Period: {data.get('period_start', '')[:10]} to {data.get('period_end', '')[:10]}")
    print("=" * 40)


def cmd_history(token: str, limit: int = 10):
    """List recent calls."""
    data = api_request("GET", f"/v1/calls?limit={limit}", token)

    # API returns 'calls' key
    items = data.get("calls", data.get("items", []))
    total = len(items)

    print(f"\n[phone] Call History ({len(items)} of {total})")
    print("=" * 60)

    if not items:
        print("   No calls yet.")
    else:
        for call in items:
            status_icon = {
                "success": "[ok]",
                "terminated": "[x]",
                "no_answer": "[na]",
                "busy": "[na]",
                "failed": "[!]",
                "voicemail": "[vm]",
                "cancelled": "[x]",
            }.get(call.get("status"), "[?]")

            # Handle nested metadata.created_at
            metadata = call.get("metadata", {}) or {}
            created = metadata.get("created_at", call.get("created_at", ""))[:16].replace("T", " ")

            # Extract summary from highlights
            highlights = call.get("highlights", "")
            summary = highlights.split("\n")[0][:30] if highlights else call.get("status", "")

            print(f"   {status_icon} {created}  {summary:<30}  {call.get('call_id', '')[:8]}")

    print("=" * 60)
    print("   Use --call-info <ID> to see details")


def cmd_call_info(token: str, call_id: str):
    """Get detailed call information."""
    data = api_request("GET", f"/v1/calls/{call_id}", token)

    metadata = data.get("metadata", {}) or {}
    submission = data.get("submission", {}) or {}

    print(f"\n[phone] Call Details")
    print("=" * 50)
    print(f"   ID: {data.get('call_id')}")
    print(f"   Status: {data.get('status')}")

    # Phone from submission
    if submission.get("respondent_phone"):
        print(f"   To: {submission.get('respondent_phone')}")
    if submission.get("business_name"):
        print(f"   Business: {submission.get('business_name')}")
    if submission.get("task_description"):
        print(f"   Task: {submission.get('task_description')[:50]}")

    # Created from metadata
    if metadata.get("created_at"):
        print(f"   Created: {metadata.get('created_at')}")

    if data.get("duration_seconds"):
        print(f"   Duration: {data.get('duration_seconds'):.1f}s")

    if data.get("highlights"):
        print(f"\n[info] Summary:")
        for line in data.get("highlights", "").split("\n")[:5]:
            if line.strip():
                print(f"   {line.strip()}")

    if data.get("next_steps"):
        print(f"\n[->] Next steps:")
        print(f"   {data.get('next_steps')}")

    print("=" * 50)
    print(f"   Use --transcript {call_id} to see conversation")


def cmd_transcript(token: str, call_id: str):
    """Get call transcript."""
    try:
        data = api_request("GET", f"/v1/calls/{call_id}/transcript", token)
    except Exception as e:
        if "forbidden" in str(e).lower():
            print(f"\n[!] Cannot access transcript (requires transcript scope)")
            print(f"   Try logging out and back in: --logout then --login")
            return
        raise

    print(f"\n[doc] Transcript for {call_id[:8]}...")
    print("=" * 50)

    # Handle different response formats
    entries = []
    if isinstance(data, dict):
        entries = data.get("entries", data.get("transcript", []))
    elif isinstance(data, list):
        entries = data

    if not entries:
        print("   No transcript available.")
    else:
        for entry in entries:
            if isinstance(entry, dict):
                speaker = entry.get("speaker", entry.get("role", "?"))
                content = entry.get("content", entry.get("text", ""))
                ts = entry.get("timestamp", "")
                icon = "[AI]" if speaker.upper() in ("AI", "ASSISTANT") else "[H]"
                print(f"   [{ts}] {icon} {content}")
            else:
                print(f"   {entry}")

    print("=" * 50)


def cmd_billing(token: str):
    """Open billing portal."""
    data = api_request("GET", "/v1/stripe/billing-portal", token)
    url = data.get("url")

    if url:
        print(f"\n[card] Opening billing portal...")
        webbrowser.open(url)
        print(f"   URL: {url}")
    else:
        print("\n[!] Could not get billing portal URL")


def cmd_make_call(token: str, phone: str, task: str, category: str, language: str, **kwargs):
    """Make a phone call."""
    submission = {
        "task_category": category,
        "task_description": task,
        "respondent_phone": phone,
        "language": language,
        "call_language": language,
    }

    for key in ["user_name", "business_name", "party_size", "appointment_date",
                "appointment_time", "time_preference_text"]:
        if key in kwargs and kwargs[key]:
            submission[key] = kwargs[key]

    print(f"\n[phone] Calling {phone}...")
    print(f"   Task: {task}\n")

    result = api_request(
        "POST", "/v1/calls", token,
        json={
            "submission": submission,
            "timezone": kwargs.get("timezone", "Europe/Madrid"),
        },
        headers={"Idempotency-Key": f"cli-{secrets.token_hex(8)}"}
    )

    print("=" * 50)
    print("[ok] Call completed!")
    print(f"   Call ID: {result.get('call_id')}")
    print(f"   Status: {result.get('status')}")

    if result.get("highlights"):
        print(f"\n[info] Result:")
        print(f"   {result.get('highlights')}")

    if result.get("next_steps"):
        print(f"\n[->] Next steps:")
        print(f"   {result.get('next_steps')}")

    if result.get("duration_seconds"):
        print(f"\n[time] Duration: {result.get('duration_seconds'):.1f}s")

    print("=" * 50)
    return result


# =============================================================================
# Main
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="KallyAI CLI - AI phone calls from your terminal",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  Make a call:     %(prog)s -p "+15551234567" -t "Ask about hours"
  Check usage:     %(prog)s --usage
  Check sub:       %(prog)s --subscription
  Call history:    %(prog)s --history
  Call details:    %(prog)s --call-info <CALL_ID>
  Transcript:      %(prog)s --transcript <CALL_ID>
  Billing portal:  %(prog)s --billing
  Login:           %(prog)s --login
  Logout:          %(prog)s --logout
        """
    )

    # Call options
    call_group = parser.add_argument_group("Call options")
    call_group.add_argument("--phone", "-p", help="Phone number (E.164: +15551234567)")
    call_group.add_argument("--task", "-t", help="What to ask/accomplish")
    call_group.add_argument("--category", "-c", default="general",
                           choices=["restaurant", "clinic", "hotel", "general"])
    call_group.add_argument("--language", "-l", default="es", choices=["en", "es"])
    call_group.add_argument("--name", help="Your name (for reservations)")
    call_group.add_argument("--business", help="Business name")
    call_group.add_argument("--party-size", type=int, help="Party size")
    call_group.add_argument("--date", help="Date (YYYY-MM-DD)")
    call_group.add_argument("--time", help="Time (HH:MM)")

    # Info commands
    info_group = parser.add_argument_group("Info commands")
    info_group.add_argument("--usage", "--stats", action="store_true",
                           help="Show usage statistics")
    info_group.add_argument("--subscription", "--sub", action="store_true",
                           help="Show subscription status")
    info_group.add_argument("--history", "--list", action="store_true",
                           help="List recent calls")
    info_group.add_argument("--call-info", metavar="ID", help="Get call details")
    info_group.add_argument("--transcript", metavar="ID", help="Get call transcript")
    info_group.add_argument("--billing", action="store_true",
                           help="Open billing portal")

    # Auth commands
    auth_group = parser.add_argument_group("Auth commands")
    auth_group.add_argument("--login", action="store_true", help="Force re-authentication")
    auth_group.add_argument("--logout", action="store_true", help="Clear saved credentials")
    auth_group.add_argument("--auth-status", action="store_true", help="Check login status")
    auth_group.add_argument("--version", "-v", action="store_true", help="Show version")

    args = parser.parse_args()

    try:
        # Version
        if args.version:
            print(f"kallyai-cli {__version__}")
            return

        # Auth commands (no token needed)
        if args.logout:
            TOKEN_FILE.unlink(missing_ok=True)
            print("[ok] Logged out")
            return

        if args.auth_status:
            if load_token():
                print("[ok] Logged in")
            else:
                print("[x] Not logged in")
            return

        if args.login:
            authenticate()
            return

        # Commands that need authentication
        if args.usage:
            cmd_usage(require_token())
        elif args.subscription:
            cmd_subscription(require_token())
        elif args.history:
            cmd_history(require_token())
        elif args.call_info:
            cmd_call_info(require_token(), args.call_info)
        elif args.transcript:
            cmd_transcript(require_token(), args.transcript)
        elif args.billing:
            cmd_billing(require_token())
        elif args.phone and args.task:
            cmd_make_call(
                require_token(),
                args.phone, args.task, args.category, args.language,
                user_name=args.name,
                business_name=args.business,
                party_size=args.party_size,
                appointment_date=args.date,
                appointment_time=args.time,
            )
        else:
            parser.print_help()
            if not args.phone and not args.task:
                print("\n[tip] Use --usage to check your minutes, or --help for all commands")

    except Exception as e:
        print(f"\n[!] Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
