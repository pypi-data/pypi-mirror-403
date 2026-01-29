# KallyAI API Reference

## Table of Contents

1. [Authentication](#authentication)
2. [Call Endpoints](#call-endpoints)
3. [User Endpoints](#user-endpoints)
4. [Request Schemas](#request-schemas)
5. [Response Schemas](#response-schemas)
6. [Error Codes](#error-codes)

---

## Authentication

**Type:** OAuth2 Bearer Token

**Header:**
```
Authorization: Bearer <access_token>
```

### Authentication Methods

Users sign in with their Google or Apple account:

| Method | Use Case | Endpoint |
|--------|----------|----------|
| OAuth2 Authorization Code | GPT Actions, web apps | See flow below |
| Google Sign-In | Mobile apps (iOS/Android) | `POST /v1/auth/google/validate` |
| Apple Sign-In | iOS apps | `POST /v1/auth/apple/token` |

### CLI Authentication (Terminal Tools & AI Agents)

For CLI tools and AI agents, use the simplified CLI auth flow:

**Step 1: Open auth page with localhost redirect**
```
GET /v1/auth/cli?redirect_uri=http://localhost:PORT&state=OPTIONAL_STATE
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `redirect_uri` | Yes | Must be `http://localhost:PORT` or `http://127.0.0.1:PORT` |
| `state` | No | Optional state parameter passed back in redirect |

User sees Google/Apple sign-in page. After authentication, redirects to:
```
http://localhost:PORT?access_token=TOKEN&refresh_token=TOKEN&expires_in=3600&state=STATE
```

**Security:** Only localhost/127.0.0.1 redirect URIs are allowed.

---

### OAuth2 Authorization Code Flow (GPT Actions)

**Step 1: Redirect user to authorization**
```
GET /v1/auth/authorize?response_type=code&client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&state=RANDOM_STATE&scope=calls:read%20calls:write
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `response_type` | Yes | Must be `code` |
| `client_id` | Yes | Your OAuth client ID |
| `redirect_uri` | Yes | URL to redirect after auth |
| `state` | No | CSRF protection token |
| `scope` | No | Space-separated scopes |

User sees Google sign-in page. After authentication, redirects to `redirect_uri?code=AUTH_CODE&state=STATE`.

**Step 2: Exchange code for tokens**
```
POST /v1/auth/gpt/token
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&client_id=YOUR_ID&client_secret=YOUR_SECRET&code=AUTH_CODE&redirect_uri=YOUR_URI
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "expires_in": 3600,
  "scope": "calls:read calls:write"
}
```

**Step 3: Refresh expired tokens**
```
POST /v1/auth/gpt/token
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&client_id=YOUR_ID&client_secret=YOUR_SECRET&refresh_token=REFRESH_TOKEN
```

---

### Token Refresh

To refresh an expired access token:

```
POST /v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "REFRESH_TOKEN"
}
```

---

### Scopes

| Scope | Description |
|-------|-------------|
| `calls:read` | Read call history and details |
| `calls:write` | Make phone calls |
| `sessions:read` | Read session state |
| `sessions:write` | Update session state |
| `subscription:read` | Read subscription status |
| `billing:manage` | Access billing portal |
| `transcripts:read` | Read call transcripts |
| `recordings:read` | Access call recordings |

---

## Call Endpoints

### Create Call

**`POST /v1/calls`**

Creates an AI phone call to accomplish a task.

**Headers:**
```
Authorization: Bearer <token>
Idempotency-Key: <uuid>  (optional, auto-generated for GPT clients)
```

**Request Body:** See [CallCreateRequest](#callcreaterequest)

**Response:** `201 Created` - See [CallResponse](#callresponse)

**Errors:**
- `400` - Validation error
- `401` - Unauthorized
- `402` - Quota exceeded
- `403` - Country/safety restriction
- `422` - Missing phone, emergency number, safety violation

---

### List Calls

**`GET /v1/calls`**

**Query Parameters:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | int | 50 | Max results (1-200) |
| `offset` | int | 0 | Pagination offset |

**Response:**
```json
{
  "calls": [
    {
      "call_id": "uuid",
      "status": "success",
      "metadata": {
        "created_at": "2026-01-25T15:30:00Z"
      },
      "submission": {
        "respondent_phone": "+14155551234",
        "business_name": "Italian Bistro"
      }
    }
  ],
  "total": 42
}
```

---

### Get Call Details

**`GET /v1/calls/{call_id}`**

**Response:**
```json
{
  "call_id": "uuid",
  "status": "success",
  "highlights": "Reserved table for 4 at 7pm",
  "next_steps": "Confirmation sent to email",
  "duration_seconds": 185.5,
  "metadata": {
    "created_at": "2026-01-25T15:30:00Z"
  },
  "submission": {
    "respondent_phone": "+14155551234",
    "business_name": "Italian Bistro",
    "task_description": "Reserve table for 4"
  }
}
```

---

### Get Transcript

**`GET /v1/calls/{call_id}/transcript`**

**Response:**
```json
{
  "entries": [
    {"speaker": "AI", "content": "Hello, I'm calling to make a reservation.", "timestamp": "00:00:01"},
    {"speaker": "HUMAN", "content": "Hi, how can I help you?", "timestamp": "00:00:05"}
  ]
}
```

---

### Get Calendar Event

**`GET /v1/calls/{call_id}/calendar.ics`**

Returns ICS calendar file for importing appointments.

---

## User Endpoints

### Get Subscription

**`GET /v1/users/me/subscription`**

```json
{
  "has_active_subscription": true,
  "provider": "stripe",
  "plan": {
    "type": "personal",
    "period": "monthly",
    "minutes_included": 210
  },
  "status": "active",
  "expires_at": "2026-02-22T00:00:00Z",
  "auto_renew": true,
  "management_url": "https://billing.stripe.com/..."
}
```

---

### Get Statistics

**`GET /v1/users/me/statistics`**

```json
{
  "plan_type": "personal",
  "minutes_allocated": 210,
  "minutes_used": 45,
  "minutes_remaining": 165,
  "calls_allocated": 35,
  "calls_used": 8,
  "calls_remaining": 27,
  "period_start": "2026-01-01T00:00:00Z",
  "period_end": "2026-02-01T00:00:00Z",
  "usage_percentage": 21.4,
  "subscription_status": "active"
}
```

---

### Get Billing Portal

**`GET /v1/stripe/billing-portal`**

```json
{
  "url": "https://billing.stripe.com/p/session/..."
}
```

---

## Request Schemas

### CallCreateRequest

```json
{
  "submission": SubmissionPayload,
  "timezone": "string (e.g., America/New_York)",
  "session_id": "string (optional)"
}
```

### SubmissionPayload

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `task_category` | enum | Yes | `restaurant`, `clinic`, `hotel`, `general` |
| `task_description` | string | Yes | What the AI should accomplish |
| `respondent_phone` | string | Yes | Phone to call (E.164: +1234567890) |
| `business_name` | string | No | Name of business |
| `user_name` | string | No | User's name for reservation |
| `user_phone` | string | No | User's callback number |
| `appointment_date` | date | No | YYYY-MM-DD format |
| `appointment_time` | string | No | HH:MM (24-hour) |
| `time_preference_text` | string | No | Natural language: "morning", "after 5pm" |
| `party_size` | int | No | 1-50, for restaurant reservations |
| `language` | enum | No | `en`, `es` (app language) |
| `call_language` | enum | No | `en`, `es` (call language) |
| `is_urgent` | bool | No | Prioritize the call |
| `additional_instructions` | array | No | Extra instructions for AI |

---

## Response Schemas

### CallResponse

```json
{
  "call_id": "uuid-string",
  "status": "success|no_answer|busy|failed|voicemail|cancelled",
  "highlights": "Summary of what was accomplished",
  "next_steps": "Any follow-up actions needed",
  "duration_seconds": 185.5,
  "metadata": {
    "created_at": "2026-01-22T15:30:00Z"
  },
  "submission": { /* original submission */ }
}
```

### QuotaExceededResponse (402)

```json
{
  "plan_type": "trial",
  "minutes_allocated": 30,
  "minutes_used": 30,
  "upgrade_url": "https://kallyai.com/pricing"
}
```

---

## Error Codes

### Standard Error Format

```json
{
  "error": {
    "code": "error_code",
    "details": {
      "message": "Human readable message",
      "reason": "Additional context"
    },
    "correlation_id": "uuid"
  }
}
```

### Error Code Reference

| Code | HTTP | Description |
|------|------|-------------|
| `quota_exceeded` | 402 | User out of minutes |
| `missing_phone_number` | 422 | No phone in submission |
| `emergency_number` | 422 | Cannot call 911/emergency |
| `toll_number` | 422 | Cannot call premium rate |
| `blocked_number` | 403 | Number flagged as fraud |
| `suppression_violation` | 403 | Number on DNC list |
| `safety_violation` | 422 | Content violates guidelines |
| `scheduling_violation` | 422 | Invalid date/time |
| `consent_denied` | 422 | User declined consent |
| `country_restriction` | 403 | Country not supported by region |
| `unsupported_country` | 403 | Country not supported globally |
| `unsupported_language` | 422 | Language not supported |
| `missing_token` | 401 | No Authorization header |
| `forbidden` | 403 | Insufficient permissions |
| `call_not_found` | 404 | Call doesn't exist |
| `transcript_not_found` | 404 | No transcript available |

---

## Supported Countries

Calls supported to US, Canada, UK, Spain, and most European countries. Emergency numbers (911, 112, etc.) are blocked.

## Supported Languages

- English (`en`)
- Spanish (`es`)

Set `language` for app interface, `call_language` for the actual phone conversation.
