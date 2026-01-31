# SweatStack FastAPI Plugin

A lightweight plugin for integrating SweatStack OAuth into FastAPI applications.

## Executive Summary

This plugin provides stateless OAuth authentication for FastAPI applications using SweatStack as the identity provider.

**Architecture:**
- OAuth 2.0 authorization code flow with CSRF protection via `state` parameter
- Tokens stored in Fernet-encrypted cookies (AES-128-CBC + HMAC) — no server-side session storage required
- Automatic token refresh when access tokens near expiry
- FastAPI dependency injection for clean route handler integration

**Security model:**
- Cookies: `httponly`, `secure`, `samesite=lax`
- OAuth state validated via short-lived cookie to prevent CSRF
- Redirect URLs validated to prevent open redirect attacks
- Tokens never exposed to browser JavaScript

**Interface:**
```python
from sweatstack.fastapi import configure, instrument, AuthenticatedUser

configure(client_id=..., client_secret=..., session_secret=..., app_url=...)
instrument(app)  # Adds {prefix}/login, callback, logout (default: /auth/sweatstack)

def my_route(user: AuthenticatedUser):
    return user.client.get_activities()
```

**Scope of v1:** Sync-only, no PKCE (client secret flow), module-level configuration. Async, PKCE, and class-based config can be added later without breaking changes.

## Usage Example

```
app/
├── main.py
├── routers/
│   ├── activities.py
│   └── athletes.py
```

```python
# main.py
import os
from fastapi import FastAPI
from sweatstack.fastapi import configure, instrument

from .routers import activities, athletes

app = FastAPI()

configure(
    client_id="...",
    client_secret="...",
    app_url="http://localhost:8000",
    session_secret=os.environ["SESSION_SECRET"],
)

instrument(app)

app.include_router(activities.router, prefix="/activities")
app.include_router(athletes.router, prefix="/athletes")
```

```python
# routers/activities.py
from fastapi import APIRouter
from sweatstack.fastapi import AuthenticatedUser, OptionalUser

router = APIRouter()


@router.get("/")
def list_activities(user: AuthenticatedUser):
    return user.client.get_activities(limit=10)


@router.get("/public")
def public_feed(user: OptionalUser):
    if user:
        return user.client.get_activities(limit=5)
    return {"message": "Login to see your activities"}
```

```python
# routers/athletes.py
from fastapi import APIRouter
from sweatstack.fastapi import AuthenticatedUser

router = APIRouter()


@router.get("/me")
def get_me(user: AuthenticatedUser):
    return user.client.get_userinfo()
```

## Routes Added by `instrument(app)`

| Method | Path | Description |
|--------|------|-------------|
| GET | `{prefix}/login` | Redirects to SweatStack OAuth |
| GET | `{prefix}/callback` | Handles OAuth callback |
| POST | `{prefix}/logout` | Clears session, redirects to `/` |

Default prefix is `/auth/sweatstack`, configurable via `auth_route_prefix` parameter.

The login endpoint accepts an optional `?next=/path` parameter to redirect after successful authentication.


## Technical Summary

**All exports from `sweatstack.fastapi`:**

```python
from sweatstack.fastapi import (
    configure,   # Configure OAuth and session settings
    instrument,  # Add auth routes to FastAPI app
    AuthenticatedUser,   # Dependency: requires authenticated user
    OptionalUser,        # Dependency: returns user or None
    SweatStackUser,      # The user dataclass (for type hints)
)
```

| Export | Type | Description |
|--------|------|-------------|
| `AuthenticatedUser` | `Annotated[SweatStackUser, Depends(...)]` | Requires valid session, returns user or 401/redirect |
| `OptionalUser` | `Annotated[SweatStackUser \| None, Depends(...)]` | Returns user if logged in, `None` otherwise |
| `SweatStackUser` | `dataclass` | For type hints when needed |

Use `AuthenticatedUser` for routes that require authentication. Behavior when unauthenticated depends on `redirect_unauthenticated` config (default: 401, or redirect to login with `?next=` if True).

**SweatStackUser:**

```python
@dataclass
class SweatStackUser:
    user_id: str
    client: Client  # Authenticated SweatStack client instance
```


## Configuration Parameters

```python
configure(
    # Required (or use environment variables)
    client_id: str,                    # OAuth client ID (env: SWEATSTACK_CLIENT_ID)
    client_secret: str,                # OAuth client secret (env: SWEATSTACK_CLIENT_SECRET)
    app_url: str,                      # Base URL of the app (env: APP_URL)
    session_secret: str | list[str],   # Fernet key(s) (env: SWEATSTACK_SESSION_SECRET)

    # Optional
    scopes: list[str] = ["profile", "data:read"],  # OAuth scopes to request
    cookie_secure: bool | None = None, # Auto-detected from app_url scheme
    cookie_max_age: int = 86400,       # Session cookie lifetime in seconds (default: 24h)
    auth_route_prefix: str = "/auth/sweatstack",  # Prefix for auth routes
    redirect_unauthenticated: bool = False,  # If True, redirect to login instead of 401
)
```

All required parameters can be set via environment variables, allowing zero-argument configuration:

```python
# With environment variables set, this is all you need:
configure()
```

The OAuth redirect URI is automatically derived as `app_url + auth_route_prefix + "/callback"`.

**Base URL:** All API calls use `https://app.sweatstack.no`.


## Session Storage

OAuth tokens must be stored securely and not exposed to the browser. We use Fernet-encrypted cookies for stateless session management.

**Why Fernet?**
- Symmetric encryption (AES-128-CBC + HMAC)
- Simple API from the `cryptography` library
- Provides both confidentiality and integrity
- No server-side storage required

**Configuration:**

```python
configure(
    client_id="...",
    client_secret="...",
    app_url="http://localhost:8000",
    session_secret=os.environ["SESSION_SECRET"],  # Fernet key
)
```

**Generate a session secret:**

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Cookie names:**
- `sweatstack_session` — encrypted session data
- `sweatstack_oauth_state` — temporary state during OAuth flow (5 min TTL)

**Cookie settings (both cookies):**
- `httponly=True` — no JavaScript access
- `secure` — auto-detected from `app_url` scheme (https=True, http=False)
- `samesite="lax"` — CSRF protection
- `path="/"` — available on all routes

A warning is logged when using HTTP with a non-localhost URL.

**Session cookie additional settings:**
- `max_age=86400` — 24-hour expiry (configurable via `cookie_max_age`)

**Session data structure (encrypted):**

```json
{
    "access_token": "...",
    "refresh_token": "...",
    "user_id": "abc123"
}
```

**Key rotation:**

For zero-downtime key rotation, `session_secret` accepts a list. First key encrypts; all keys are tried for decryption:

```python
configure(
    ...
    session_secret=[
        os.environ["SESSION_SECRET_NEW"],
        os.environ["SESSION_SECRET_OLD"],
    ],
)
```


## OAuth Flow

### Login (`GET {prefix}/login`)

1. Generate random `state` value (32 bytes, URL-safe base64)
2. If `?next=` parameter provided, validate and encode it in state: `state = base64(json({"nonce": "...", "next": "/dashboard"}))`
3. Set `sweatstack_oauth_state` cookie with the full encoded state (5 min TTL)
4. Redirect to `https://app.sweatstack.no/oauth/authorize` with parameters:
   - `client_id`, `redirect_uri`, `scope`, `state`, `prompt=none`

**Redirect validation:** The `next` parameter must be a relative path (starts with `/`, not `//`) to prevent open redirect attacks:

```python
def validate_redirect(url: str | None) -> str | None:
    if url and url.startswith('/') and not url.startswith('//'):
        return url
    return None
```

### Callback (`GET {prefix}/callback`)

1. Compare `state` query parameter with `sweatstack_oauth_state` cookie (byte-for-byte)
2. If mismatch or missing: return 400 Bad Request
3. Clear state cookie
4. If `?error=` parameter present: redirect to `/`
5. Exchange `code` for tokens via `POST https://app.sweatstack.no/api/v1/oauth/token`
6. Extract `user_id` from access token JWT
7. Create encrypted `sweatstack_session` cookie with tokens
8. Redirect to `next` URL from state (default: `/`)

### Logout (`POST {prefix}/logout`)

1. Clear `sweatstack_session` cookie
2. Redirect to `/`


## Token Refresh

Access tokens are short-lived. The plugin automatically refreshes them when needed.

**Refresh logic (in dependency):**

```python
def require_user(request: Request, response: Response) -> SweatStackUser:
    session = decrypt_session(request.cookies.get("sweatstack_session"))
    if not session:
        raise HTTPException(401, "Not authenticated")

    access_token = session["access_token"]

    if is_token_expiring(access_token):
        try:
            # Extract timezone from current token for refresh request
            token_body = decode_jwt_body(access_token)
            tz = token_body.get("tz", "UTC")

            new_access_token = refresh_access_token(
                refresh_token=session["refresh_token"],
                client_id=config.client_id,
                client_secret=config.client_secret,
                tz=tz,
            )
            session["access_token"] = new_access_token
            # Update cookie in response
            set_session_cookie(response, session)
            access_token = new_access_token
        except Exception:
            logging.exception("Token refresh failed")
            clear_session_cookie(response)
            raise HTTPException(401, "Session expired")

    client = Client(api_key=access_token)
    return SweatStackUser(user_id=session["user_id"], client=client)
```

**Expiry check:**

```python
TOKEN_EXPIRY_MARGIN = 5  # seconds

def is_token_expiring(token: str) -> bool:
    body = decode_jwt_body(token)
    return body["exp"] - TOKEN_EXPIRY_MARGIN < time.time()
```

**Timezone handling:** The refresh endpoint requires a `tz` parameter. We extract this from the current access token's JWT body (falls back to `"UTC"` if not present).

The cookie is updated directly via FastAPI's `Response` parameter in the dependency, avoiding middleware complexity.


## Error Handling

| Scenario | Behavior |
|----------|----------|
| Missing/invalid session cookie | 401 Unauthorized |
| Token refresh fails | Log error, clear cookie, 401 Unauthorized |
| OAuth callback error | Redirect to `/` (future: configurable error page) |
| State mismatch in callback | 400 Bad Request |
| Decryption fails (tampered cookie) | Treat as missing session, 401 |


## File Structure

```
src/sweatstack/
├── __init__.py            # Main package (no FastAPI re-exports)
├── client.py              # Existing CLI client
├── utils.py               # Existing utils (decode_jwt_body, etc.)
└── fastapi/
    ├── __init__.py        # All FastAPI exports (with dependency check)
    ├── config.py          # Module-level configuration state
    ├── routes.py          # Login, callback, logout routes
    ├── dependencies.py    # require_user, optional_user, SweatStackUser
    └── session.py         # Fernet encrypt/decrypt, cookie helpers
```

**FastAPI submodule exports:**

```python
# sweatstack/fastapi/__init__.py
from .config import configure
from .routes import instrument
from .dependencies import AuthenticatedUser, OptionalUser, SweatStackUser
```


## Implementation Notes

**Sync-only:** This first version uses synchronous code throughout. The existing `Client` class is sync, and we reuse it directly. Async support can be added later.

**No PKCE yet:** The initial implementation uses the standard authorization code flow with client secret. PKCE support will be added in a future iteration.

**Module-level state:** Configuration is stored in an internal `FastAPIConfig` dataclass (not exposed to users — they just pass kwargs to `configure()`). This is simple and works well for typical single-app deployments.

**Configuration validation:** Calling `instrument()` before `configure()` raises a clear error:
```
RuntimeError: configure() must be called before instrument()
```

**Optional FastAPI dependency:** FastAPI is an optional dependency. Attempting to import from `sweatstack.fastapi` without FastAPI installed raises a clear error:
```python
# sweatstack/fastapi/__init__.py
try:
    import fastapi
except ImportError:
    raise ImportError(
        "FastAPI is required for sweatstack.fastapi. "
        "Install it with: pip install sweatstack[fastapi]"
    )
```

This follows the same pattern as the existing Streamlit integration.

**Dependencies:** Requires `cryptography` (for Fernet) and `fastapi` as optional extras. The existing `httpx` dependency handles OAuth token exchange.
