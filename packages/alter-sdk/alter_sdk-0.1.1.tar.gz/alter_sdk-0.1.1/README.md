# Alter SDK for Python

Official Python SDK for [Alter Vault](https://alter.com) - OAuth token management with policy enforcement.

## Features

- 🔐 **Secure Token Management**: Retrieve OAuth tokens from Alter Vault with policy enforcement
- 🎯 **Provider-Specific Wrappers**: Native support for Google, GitHub, and more
- 🌐 **Generic HTTP Client**: Fallback for any OAuth provider
- 📝 **Comprehensive Audit Logging**: All API calls logged automatically
- ⚡ **Backend Token Caching**: Redis-based caching for <10ms response times
- 🛡️ **Real-time Policy Enforcement**: Every token request checked against current policies
- 🔄 **Automatic Token Refresh**: Tokens refreshed transparently
- 🎭 **Decorator Pattern**: Wraps official SDKs without breaking compatibility

## Installation

```bash
# Core SDK only
pip install alter-sdk

# With Google API support
pip install alter-sdk[google]

# With GitHub support
pip install alter-sdk[github]

# With all providers
pip install alter-sdk[all]
```

## Quick Start

```python
import asyncio
from alter_sdk import AlterVault, Provider

async def main():
    # Initialize SDK
    vault = AlterVault(
        api_key="alter_key_...",
        app_id="your-app-id"
    )

    # Get provider client (tokens injected automatically - never exposed)
    google = await vault.get_client(
        provider=Provider.GOOGLE,
        user={"user_id": "alice", "email": "alice@example.com"}
    )

    # Use Google APIs normally - no token handling needed
    calendar = await google.build("calendar", "v3")
    events = calendar.events().list(calendarId="primary", maxResults=10).execute()

    for event in events.get("items", []):
        print(f"Event: {event['summary']}")

    # Clean up
    await vault.close()

asyncio.run(main())
```

**Key Principle: Zero Token Exposure**

Tokens are managed automatically by the SDK and never exposed to developers. All token caching is handled by the backend for performance. You only interact with provider APIs through `get_client()` or `call_api()` - tokens are injected behind the scenes.

**Architecture: No SDK-Side Caching**

The SDK has **zero client-side token caching** to ensure:
- ✅ Real-time policy enforcement on every request
- ✅ Complete audit trail (backend logs all token access)
- ✅ Instant revocation (no SDK cache delays)
- ✅ Fast performance via backend Redis cache (<10ms)

Every token request goes to the backend, which handles caching efficiently with Redis (5-15min TTL). This architecture ensures security without sacrificing performance.

## Usage Examples

### Google Calendar API

```python
from alter_sdk import AlterVault, Provider

async def list_calendar_events():
    vault = AlterVault(
        api_key="alter_key_...",
        app_id="your-app-id"
    )

    # Get Google client wrapper (tokens hidden)
    google = await vault.get_client(
        provider=Provider.GOOGLE,
        user={"user_id": "alice", "email": "alice@example.com"}
    )

    # Use Google API normally - token injected automatically
    calendar = await google.build("calendar", "v3")
    events = calendar.events().list(
        calendarId="primary",
        maxResults=10
    ).execute()

    for event in events.get("items", []):
        print(f"Event: {event['summary']}")

    await vault.close()
```

### GitHub API

```python
from alter_sdk import AlterVault, Provider

async def list_github_repos():
    vault = AlterVault(
        api_key="alter_key_...",
        app_id="your-app-id"
    )

    # Get GitHub client wrapper (tokens hidden)
    github = await vault.get_client(
        provider=Provider.GITHUB,
        user={"user_id": "bob", "username": "bob"}
    )

    # Use PyGithub normally
    user = github.get_user()
    repos = user.get_repos()

    for repo in repos:
        print(f"Repo: {repo.name} - {repo.description}")

    await vault.close()
```

### Generic API Calls

For providers without dedicated wrappers, use `call_api()`:

```python
from alter_sdk import AlterVault, Provider

async def call_custom_api():
    vault = AlterVault(
        api_key="alter_key_...",
        app_id="your-app-id"
    )

    # Call any provider API - OAuth token injected automatically
    response = await vault.call_api(
        provider=Provider.STRIPE,
        method="GET",
        endpoint="https://api.stripe.com/v1/customers",
        user={"org_id": "acme"},
        params={"limit": 10}
    )
    customers = response.json()["data"]

    # POST request example
    response = await vault.call_api(
        provider=Provider.SHOPIFY,
        method="POST",
        endpoint="https://my-store.myshopify.com/admin/api/2024-01/products.json",
        user={"store_id": "my-store"},
        body={"product": {"title": "New Product", "price": "29.99"}}
    )
    product = response.json()["product"]

    await vault.close()
```

### Using as Context Manager

```python
from alter_sdk import AlterVault, Provider

async def with_context_manager():
    async with AlterVault(api_key="alter_key_...", app_id="your-app-id") as vault:
        # Use provider client - tokens handled automatically
        google = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})
        calendar = await google.build("calendar", "v3")
        events = calendar.events().list(calendarId="primary").execute()
    # Automatically closed
```

## Configuration

```python
vault = AlterVault(
    api_key="alter_key_...",          # Required: Your Alter Vault API key
    app_id="your-app-id",              # Required: Your application ID (UUID)
    base_url="https://api.alter.com",  # Optional: Custom API URL
    enable_audit_logging=True,         # Optional: Enable audit logs (default: True)
    timeout=30.0                       # Optional: HTTP timeout in seconds
)
```

## Error Handling

```python
from alter_sdk import AlterVault, Provider
from alter_sdk.exceptions import (
    PolicyViolationError,              # Policy denied access (403)
    PolicyServiceUnavailableError,     # Policy service unavailable (503)
    ConnectionNotFoundError,           # No OAuth connection found
    TokenExpiredError,                 # Token refresh failed
    NetworkError,                      # Backend unreachable
    ProviderAPIError                   # Provider API error
)

try:
    # Get client - tokens handled automatically
    google = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})
    calendar = await google.build("calendar", "v3")
    events = calendar.events().list(calendarId="primary").execute()
except PolicyViolationError as e:
    # Policy denied access - check policy configuration
    print(f"Policy violation: {e.message}")
    print(f"Details: {e.details}")
    # Handle: User needs to contact admin to adjust policy or verify attributes
except PolicyServiceUnavailableError as e:
    # Policy service unavailable - retry after delay
    print(f"Policy service unavailable: {e.message}")
    print(f"Retry after: {e.retry_after} seconds")
    # Handle: Retry after delay or use fallback logic
except ConnectionNotFoundError as e:
    # No OAuth connection found - user needs to authenticate
    print(f"Connection not found: {e.message}")
    # Handle: Redirect user to OAuth flow
except TokenExpiredError as e:
    # Token refresh failed - user needs to re-authenticate
    print(f"Token expired: {e.connection_id}")
    # Handle: Redirect user to re-authenticate
except NetworkError as e:
    # Backend unreachable - network or infrastructure issue
    print(f"Network error: {e.message}")
    # Handle: Retry with backoff or show error message
```

### Policy-Related Exceptions

**⚠️ CRITICAL: Always Handle Policy Exceptions**

Policy enforcement happens on **every token retrieval** and can raise two exceptions:

#### 1. PolicyViolationError (HTTP 403)

**When:** Token access denied by configured policy rules (scopes, time, IP, attributes)

**Exception Details:**
```python
class PolicyViolationError(AlterSDKException):
    message: str       # Human-readable denial reason
    error_code: str    # "policy_violation"
    details: dict      # {resource_id, action, violation_type}
```

**Common Causes:**
- OAuth scope not in policy's `allowed_scopes` list
- Request outside business hours (`business_hours_only` policy)
- Request on weekend (`weekdays_only` policy)
- Client IP not in `ip_allowlist`
- Connection missing required attributes (`required_attributes` policy)

**Example:**
```python
try:
    google = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})
except PolicyViolationError as e:
    if "scope" in e.message.lower():
        print("❌ Scope not allowed. Contact admin to update policy.")
    elif "business hours" in e.message.lower():
        print("❌ Access restricted to business hours (9am-5pm)")
    elif "ip" in e.message.lower():
        print("❌ IP address not in allowlist. Use VPN or office network.")
    elif "attribute" in e.message.lower():
        print("❌ Connection missing required attributes")
```

**Resolution:**
- Check policy configuration in Alter Vault Dashboard → App → Policies
- Verify connection attributes match policy requirements
- Contact administrator to adjust policy if legitimate use case
- Ensure client IP is in allowlist (if using IP-based policies)

---

#### 2. PolicyServiceUnavailableError (HTTP 503)

**When:** Cerbos policy service unavailable (system fails closed - denies all access)

**Exception Details:**
```python
class PolicyServiceUnavailableError(AlterSDKException):
    message: str       # "Policy enforcement service temporarily unavailable"
    retry_after: int   # Suggested retry delay in seconds (default: 60)
```

**System Behavior:** **FAIL CLOSED** - If policy service is down, all token access is denied to maintain security.

**Example:**
```python
import asyncio

try:
    google = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})
except PolicyServiceUnavailableError as e:
    print(f"⚠️ Policy service unavailable. Retrying after {e.retry_after} seconds...")
    await asyncio.sleep(e.retry_after)
    # Retry logic here
```

**Resolution:**
- Retry after `retry_after` seconds (exponential backoff recommended)
- Check system status page
- Contact support if issue persists beyond 5 minutes
- Implement fallback logic for degraded mode (optional)

---

### Best Practices for Policy Exception Handling

**1. Always catch policy exceptions explicitly:**
```python
# ✅ GOOD: Explicit policy exception handling
try:
    client = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})
except PolicyViolationError as e:
    # Handle policy violation
    log.warning(f"Policy violation for user alice: {e.message}")
    return None
except PolicyServiceUnavailableError as e:
    # Handle service unavailable
    log.error(f"Policy service down, retry after {e.retry_after}s")
    raise

# ❌ BAD: Catching all exceptions hides policy issues
try:
    client = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})
except Exception as e:  # Don't do this!
    pass
```

**2. Log policy violations for debugging:**
```python
try:
    client = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})
except PolicyViolationError as e:
    logger.warning(
        "Policy violation",
        extra={
            "user": "alice",
            "provider": "google",
            "error": e.message,
            "details": e.details
        }
    )
    # Show user-friendly error
    raise
```

**3. Implement retry logic for service unavailable:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=60)
)
async def get_google_client_with_retry(vault, user):
    try:
        return await vault.get_client(Provider.GOOGLE, user=user)
    except PolicyServiceUnavailableError:
        # Retry on 503
        raise
    except PolicyViolationError:
        # Don't retry on 403 (policy violation)
        raise
```

**4. Provide clear user feedback:**
```python
try:
    client = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})
except PolicyViolationError as e:
    if "scope" in e.message.lower():
        return {"error": "Your integration doesn't have permission to access this data. Contact your administrator."}
    elif "business hours" in e.message.lower():
        return {"error": "This feature is only available during business hours (9am-5pm)."}
    elif "ip" in e.message.lower():
        return {"error": "This feature requires VPN connection."}
```

**See Also:** [Policy Enforcement Documentation](../../apps/backend/docs/POLICY_ENFORCEMENT.md) for complete policy configuration details.

## Audit Logging

All API calls are automatically logged to the backend:

```python
from alter_sdk import AlterVault, Provider

# All calls through get_client() are logged automatically
google = await vault.get_client(Provider.GOOGLE, user={"user_id": "alice"})
calendar = await google.build("calendar", "v3")
events = calendar.events().list(calendarId="primary").execute()
# ↑ Logged automatically to backend

# All calls through call_api() are also logged automatically
response = await vault.call_api(
    provider=Provider.STRIPE,
    method="GET",
    endpoint="https://api.stripe.com/v1/customers",
    user={"org_id": "acme"}
)
# ↑ Logged automatically to backend
```

Audit logs never raise exceptions - if logging fails, a warning is logged but your application continues running.

## Policy Enforcement

Policies are enforced at backend using Cerbos:

| Policy Type | Examples |
|-------------|----------|
| Scope restrictions | Only allowed OAuth scopes |
| Time-based access | Business hours, weekdays |
| Rate limiting | Max retrievals per day |
| User context | Tier-based, role-based, verified users |
| Geographic | IP allowlist, country-based |

Policies configured in Alter Vault dashboard per app.

## Architecture

See [ALTER_PYTHON_SDK_ARCHITECTURE.md](./ALTER_PYTHON_SDK_ARCHITECTURE.md) for comprehensive documentation on:
- Token retrieval flow
- No SDK-side caching (security design)
- Backend cache architecture
- Security guarantees
- Performance characteristics
- Error handling patterns
- Testing strategy
- Migration notes

**Key Points**:
- ✅ Zero token exposure (never visible to developers)
- ✅ No SDK-side caching (real-time policy enforcement)
- ✅ Backend Redis cache (5-10ms response times)
- ✅ Complete audit trail (all token access logged)
- ✅ Instant revocation (no SDK cache delays)

## Development

```bash
# Install dependencies
poetry install

# Run tests
pytest

# Type checking
mypy alter_sdk

# Linting
ruff check alter_sdk
black alter_sdk
```

## Requirements

- Python 3.11+
- httpx, pydantic

**Optional:** google-api-python-client, PyGithub (for provider wrappers)

## License

MIT License
