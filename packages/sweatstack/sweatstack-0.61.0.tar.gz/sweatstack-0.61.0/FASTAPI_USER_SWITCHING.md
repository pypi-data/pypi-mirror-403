# FastAPI User Switching

This document explains how user switching works in the SweatStack library and proposes an intuitive interface for the FastAPI integration.

## Understanding User Switching

### Token Types

SweatStack uses two types of tokens for user switching:

**Principal Token (Root Token)**
- The original access token obtained during OAuth authentication
- Represents the authenticated user's own identity
- Retrieved via `GET /api/v1/oauth/principal-token`

**Delegated Token**
- A secondary token issued to access another user's data
- Allows acting on behalf of a different user (e.g., a coach accessing an athlete's data)
- Retrieved via `POST /api/v1/oauth/delegated-token` with the target user's ID
- Only works for users the principal has permission to access

### How Delegation Works

```
Principal User authenticates
        │
        ▼
   Principal Token stored
        │
        │ switch_user("alice")
        ▼
   POST /api/v1/oauth/delegated-token
   Body: {"sub": "alice_user_id"}
        │
        ▼
   Delegated Token returned
        │
        ▼
   All API calls now act as "alice"
        │
        │ switch_back()
        ▼
   GET /api/v1/oauth/principal-token
        │
        ▼
   Back to principal user
```

### Current Client Methods

The `Client` class provides these methods for user switching:

```python
# Mutating methods (modify the current client)
client.switch_user("alice")  # Switch to alice, modifies client in-place
client.switch_back()          # Return to principal

# Non-mutating methods (create new client instances)
alice_client = client.delegated_client("alice")  # New client for alice
principal = client.principal_client()             # New client for principal
```

---

## FastAPI Integration Challenge

The CLI client's `switch_user()` approach works well for scripts where state persists. However, FastAPI presents different challenges:

1. **Stateless Requests**: Each HTTP request is independent
2. **Multiple Users Per Request**: An endpoint might need to access data for multiple users
3. **Session Cookie**: The principal token is stored encrypted in a cookie
4. **Safety**: We need to ensure the principal context is never lost

### Current State

The existing FastAPI integration provides:

```python
@app.get("/activities")
def activities(user: AuthenticatedUser):
    # user.client is configured with the principal user's tokens
    return user.client.get_activities()
```

To access another user's data today, you would:

```python
@app.get("/user/{user_id}/activities")
def user_activities(user_id: str, user: AuthenticatedUser):
    delegated = user.client.delegated_client(user_id)
    return delegated.get_activities()
```

This works but could be more ergonomic.

---

## Proposed Interface

Extend the existing pattern with additional dependency types and URL helpers for switching.

```python
from sweatstack.fastapi import AuthenticatedUser, OptionalUser, SelectedUser, OptionalSelectedUser, urls

# AuthenticatedUser  - Always the principal (backwards compatible)
# OptionalUser       - Principal or None (backwards compatible)
# SelectedUser       - Whoever is currently selected (principal or delegated)
# OptionalSelectedUser - Selected user or None
# urls.select_user() - URL to switch to another user
# urls.select_self() - URL to switch back to principal
```

**URL Helpers:**
```python
urls.select_user("user123")                    # /auth/sweatstack/select-user/user123
urls.select_user("user123", next="/dashboard") # /auth/sweatstack/select-user/user123?next=%2Fdashboard
urls.select_self()                             # /auth/sweatstack/select-self
urls.select_self(next="/dashboard")            # /auth/sweatstack/select-self?next=%2Fdashboard
```

**Basic Usage:**
```python
@app.get("/activities")
def activities(user: SelectedUser):
    # Returns whoever is currently selected
    return user.client.get_activities()

@app.get("/athletes")
def athletes(user: AuthenticatedUser):  # Always principal
    return user.client.get_users()
```

**Template example (forms for POST):**
```html
<h2>Athletes</h2>
<ul>
  {% for athlete in athletes %}
  <li>
    <form method="post" action="{{ urls.select_user(athlete.id) }}" style="display:inline">
      <button>{{ athlete.name }}</button>
    </form>
  </li>
  {% endfor %}
</ul>

<form method="post" action="{{ urls.select_self() }}">
  <button>Back to my view</button>
</form>
```

**To check if viewing another user:**
```python
@app.get("/status")
def status(me: AuthenticatedUser, selected: SelectedUser):
    return {
        "logged_in_as": me.user_id,
        "selected": selected.user_id,
        "is_viewing_other": me.user_id != selected.user_id,
    }
```

**Built-in routes added by `instrument(app)`:**
```
POST /auth/sweatstack/select-user/{user_id}  - Switch to another user
POST /auth/sweatstack/select-self            - Switch back to principal
```

Both routes redirect to the `Referer` header if available, or `?next=` parameter, or `/`.

---

### Programmatic Switching via client.switch_user()

In addition to URL helpers, you can switch programmatically using the existing `client.switch_user()` method. The dependency automatically detects the switch after your endpoint returns and persists it to the session.

```python
@app.post("/select/{athlete_id}")
def select(athlete_id: str, user: AuthenticatedUser):
    user.client.switch_user(athlete_id)  # Switch in code
    return RedirectResponse("/dashboard")
    # After return: dependency detects switch, updates session cookie
```

**How it works:**

The `AuthenticatedUser` dependency uses FastAPI's generator pattern:

```python
def require_authenticated_user(request: Request, response: Response):
    """AuthenticatedUser dependency - always starts with principal."""
    session = get_session(request)
    principal_tokens = session["principal"]
    principal_user_id = principal_tokens["user_id"]
    original_access_token = principal_tokens["access_token"]

    client = Client(api_key=original_access_token, ...)
    user = SweatStackUser(client=client)

    yield user  # Endpoint runs here

    current_user_id = extract_user_id(client.api_key)
    session_changed = False

    if current_user_id != principal_user_id:
        # User ended on delegated → persist if user changed
        previous_delegated_user = session.get("delegated", {}).get("user_id")
        if current_user_id != previous_delegated_user:
            session["delegated"] = {
                "access_token": client.api_key,
                "refresh_token": client.refresh_token,
                "user_id": current_user_id,
            }
            session_changed = True
    else:
        # User ended on principal - check if principal token was refreshed
        if client.api_key != original_access_token:
            session["principal"]["access_token"] = client.api_key
            session["principal"]["refresh_token"] = client.refresh_token
            session_changed = True

    if session_changed:
        set_session_cookie(response, session)


def require_selected_user(request: Request, response: Response):
    """SelectedUser dependency - starts with delegated (if exists) or principal."""
    session = get_session(request)
    principal_tokens = session["principal"]
    principal_user_id = principal_tokens["user_id"]
    delegated_tokens = session.get("delegated")

    if delegated_tokens:
        # Start with delegated
        original_access_token = delegated_tokens["access_token"]
        client = Client(api_key=original_access_token, ...)
        original_user_id = delegated_tokens["user_id"]
    else:
        # Start with principal
        original_access_token = principal_tokens["access_token"]
        client = Client(api_key=original_access_token, ...)
        original_user_id = principal_user_id

    user = SweatStackUser(client=client)

    yield user  # Endpoint runs here

    current_user_id = extract_user_id(client.api_key)
    session_changed = False

    if current_user_id != principal_user_id:
        # User ended on delegated → persist if user or token changed
        if current_user_id != original_user_id or client.api_key != original_access_token:
            session["delegated"] = {
                "access_token": client.api_key,
                "refresh_token": client.refresh_token,
                "user_id": current_user_id,
            }
            session_changed = True
    elif original_user_id != principal_user_id:
        # User ended on principal but started on delegated → clear delegation
        session.pop("delegated", None)
        session_changed = True
        # Also check if principal token was refreshed during switch_back()
        if client.api_key != principal_tokens["access_token"]:
            session["principal"]["access_token"] = client.api_key
            session["principal"]["refresh_token"] = client.refresh_token
    else:
        # Stayed on principal - check if token was refreshed
        if client.api_key != original_access_token:
            session["principal"]["access_token"] = client.api_key
            session["principal"]["refresh_token"] = client.refresh_token
            session_changed = True

    if session_changed:
        set_session_cookie(response, session)
```

**This handles all cases:**

| Dependency | Action in endpoint | Result |
|------------|-------------------|--------|
| `AuthenticatedUser` | No switch | Session unchanged |
| `AuthenticatedUser` | `switch_user("alice")` | Delegation saved → alice |
| `AuthenticatedUser` | `switch_user("alice")` then `switch_back()` | Session unchanged (ends on principal) |
| `AuthenticatedUser` | `switch_user("alice")` then `switch_user("bob")` | Delegation saved → bob |
| `SelectedUser` | No switch | Session unchanged |
| `SelectedUser` | `switch_user("bob")` | Delegation saved → bob |
| `SelectedUser` | `switch_back()` | Delegation cleared (if was delegated) |

**Use case: Temporary switches without affecting session**

Two options for batch operations where you don't want to persist delegation:

```python
# Option 1: Use delegated_client() for independent clients
@app.get("/aggregate")
def aggregate(user: AuthenticatedUser):
    results = []
    for athlete_id in athlete_ids:
        delegated = user.client.delegated_client(athlete_id)
        results.append(delegated.get_activities())
    return results
    # Session unchanged
```

```python
# Option 2: Use switch_user() but switch_back() before returning
@app.get("/aggregate")
def aggregate(user: AuthenticatedUser):
    results = []
    for athlete_id in athlete_ids:
        user.client.switch_user(athlete_id)
        results.append(user.client.get_activities())
    user.client.switch_back()  # End on principal
    return results
    # Session unchanged - ended on same user as started
```

---

## Dependency Types

| Type | Returns | Use case |
|------|---------|----------|
| `AuthenticatedUser` | Always the principal (logged-in user) | Accessing principal's data, listing users |
| `OptionalUser` | Principal or `None` | Public pages that show extra content when logged in |
| `SelectedUser` | Delegated user if selected, otherwise principal | Main data access |
| `OptionalSelectedUser` | Same as `SelectedUser`, or `None` if not authenticated | Public pages with optional selected context |

**`OptionalSelectedUser` logic:**
- Not authenticated → `None`
- Authenticated, no delegation → principal user
- Authenticated, with delegation → delegated user

```python
from sweatstack.fastapi import AuthenticatedUser, OptionalUser, SelectedUser, OptionalSelectedUser

@app.get("/activities")
def activities(user: SelectedUser):
    # Returns alice's activities if alice is selected, otherwise principal's
    return user.client.get_activities()

@app.get("/my-athletes")
def athletes(user: AuthenticatedUser):
    # Always the principal - needed to list who you can select
    return user.client.get_users()

@app.get("/")
def home(user: OptionalUser):
    # Principal or None for public homepage
    if user:
        return {"logged_in": True, "user_id": user.user_id}
    return {"logged_in": False}

@app.get("/public-profile")
def profile(user: OptionalSelectedUser):
    # Selected user or None
    if user:
        return user.client.get_user()
    return {"message": "No user selected"}
```

---

## Edge Cases & Examples

```python
# Endpoint needs both principal and selected
@app.get("/dashboard")
def dashboard(me: AuthenticatedUser, selected: SelectedUser):
    # Works - types make intent explicit
    athletes = me.client.get_users()  # List from principal
    activities = selected.client.get_activities()  # Data from selected
    return {"athletes": athletes, "activities": activities}
```

```python
# Temporary access to multiple users (session unchanged)
@app.post("/batch-action")
def batch_action(user: AuthenticatedUser):
    results = []
    for athlete_id in athlete_ids:
        user.client.switch_user(athlete_id)
        results.append(user.client.get_activities())
    user.client.switch_back()  # End on principal → session unchanged
    return results
```

```python
# What if user lacks permission to select someone?
from sweatstack.exceptions import SweatStackAPIError

@app.post("/select/{athlete_id}")
def select(athlete_id: str, user: AuthenticatedUser):
    try:
        user.client.switch_user(athlete_id)
    except SweatStackAPIError as e:
        # Show user-friendly message to the end user
        raise HTTPException(
            status_code=e.status_code or 400,
            detail="You don't have access to this user's data."
        )
    return RedirectResponse("/dashboard", status_code=303)
```

---

## Final Design

### Summary

| Component | Name |
|-----------|------|
| Principal dependency | `AuthenticatedUser` |
| Optional principal | `OptionalUser` |
| Selected dependency | `SelectedUser` |
| Optional selected | `OptionalSelectedUser` |
| URL to select user | `urls.select_user(user_id, next=...)` |
| URL to select self | `urls.select_self(next=...)` |
| Route to select user | `POST /auth/sweatstack/select-user/{user_id}` |
| Route to select self | `POST /auth/sweatstack/select-self` |
| Programmatic switch | `user.client.switch_user(user_id)` |
| Programmatic switch back | `user.client.switch_back()` |

### Why This Design?

1. **Backwards compatible**: `AuthenticatedUser` and `OptionalUser` unchanged
2. **Type annotations declare intent**: Clear what each endpoint needs
3. **Two switching methods**: URL helpers for simple cases, `switch_user()` for programmatic
4. **Automatic persistence**: Dependency detects switch after endpoint returns
5. **Consistent with existing patterns**: `urls.select_user()` like `urls.login()`/`urls.logout()`
6. **POST for switching routes**: State changes should use POST (security)

---

## Implementation Notes

### Session Cookie Structure

The session cookie stores both principal and delegated tokens:

```json
{
    "principal": {
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "user_id": "coach_123"
    },
    "delegated": {
        "access_token": "eyJ...",
        "refresh_token": "eyJ...",
        "user_id": "athlete_456"
    }
}
```

When no user is selected (or `select_self` is called), `delegated` is `null` or absent.

### Token Refresh

Both token sets need automatic refresh handling:

- `AuthenticatedUser` / `OptionalUser`: refresh the principal token if expiring
- `SelectedUser` / `OptionalSelectedUser`: refresh the delegated token (if present) or principal token

### SweatStackUser

The `SweatStackUser` class:

```python
@dataclass
class SweatStackUser:
    client: Client  # Pre-configured client

    @property
    def user_id(self) -> str:
        """The user this client currently acts as (from JWT 'sub' field).

        This is a live property - if you call client.switch_user(),
        user_id will reflect the new user.
        """
        return extract_user_id(self.client.api_key)
```

The dependency type (`AuthenticatedUser` vs `SelectedUser`) determines which tokens are used initially.

---

## Caveats & Unsupported Behavior

### Don't mix switch operations across multiple dependencies

If you use both `AuthenticatedUser` and `SelectedUser` in the same endpoint, **do not call `switch_user()` or `switch_back()` on either client**. Both dependencies have after-yield logic that manages the session, and mixing switch operations could cause conflicts.

```python
# SUPPORTED: Using both for read-only access
@app.get("/dashboard")
def dashboard(me: AuthenticatedUser, selected: SelectedUser):
    athletes = me.client.get_users()           # OK
    activities = selected.client.get_activities()  # OK
    return {"athletes": athletes, "activities": activities}

# UNSUPPORTED: Switching on multiple dependencies
@app.get("/dashboard")
def dashboard(me: AuthenticatedUser, selected: SelectedUser):
    me.client.switch_user("alice")    # Don't do this
    selected.client.switch_back()      # Conflicts with above
```

If you need to switch users, use only one dependency in that endpoint.

### Exception after `switch_user()` still persists delegation

If your endpoint calls `switch_user()` and then raises an exception, the delegation is still persisted:

```python
@app.post("/select/{athlete_id}")
def select(athlete_id: str, user: AuthenticatedUser):
    user.client.switch_user(athlete_id)  # Succeeds
    do_something_that_fails()             # Raises exception!
    return RedirectResponse("/dashboard")
    # Delegation is persisted even though endpoint failed
```

This is consistent with URL-based switching (the switch is a separate action from whatever comes after).

### Streaming responses

For endpoints returning `StreamingResponse`, the after-yield session logic runs when the response is initiated, not when streaming completes. The cookie is set in the response headers before the body streams. This is generally fine, but be aware that if streaming fails partway through, the session was already updated.

---

## Built-in Routes Implementation

The built-in routes (`POST /auth/sweatstack/select-user/{user_id}` and `POST /auth/sweatstack/select-self`) should **not** use `AuthenticatedUser` or `SelectedUser` dependencies internally. They should directly:

1. Read and decrypt the session cookie
2. Validate the user is authenticated (principal tokens exist)
3. For `select-user`: fetch delegated token using principal's credentials, store in session
4. For `select-self`: remove delegated tokens from session
5. Set the updated session cookie
6. Redirect to Referer (if same-origin) or `?next=` parameter or `/`

This avoids conflicts with the after-yield logic of the user-facing dependencies.

**Redirect validation:** When using the `Referer` header for redirects, validate that it points to the same origin (same scheme + host + port) to prevent open redirect vulnerabilities. Fall back to `?next=` (also validated) or `/` if Referer is missing or invalid.

---

## Clean Implementation Architecture

The pseudocode above illustrates the logic, but a clean implementation should use proper abstractions. Here's the recommended architecture:

### Type Definitions

```python
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends


@dataclass(frozen=True, slots=True)
class TokenSet:
    """Immutable token pair with user ID."""
    access_token: str
    refresh_token: str
    user_id: str

    @property
    def is_expired(self) -> bool:
        """Check if access token is expired or expiring soon."""
        ...

    def to_dict(self) -> dict[str, str]:
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "user_id": self.user_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "TokenSet":
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            user_id=data["user_id"],
        )
```

### Session Data Model

```python
@dataclass
class SessionData:
    """Type-safe session data wrapper."""
    principal: TokenSet
    delegated: TokenSet | None = None

    def to_dict(self) -> dict:
        data = {"principal": self.principal.to_dict()}
        if self.delegated:
            data["delegated"] = self.delegated.to_dict()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "SessionData":
        return cls(
            principal=TokenSet.from_dict(data["principal"]),
            delegated=TokenSet.from_dict(data["delegated"]) if data.get("delegated") else None,
        )
```

### SweatStackUser

```python
@dataclass(slots=True)
class SweatStackUser:
    """User context for FastAPI endpoints."""
    client: Client

    @property
    def user_id(self) -> str:
        """Current user ID (reads from client's JWT)."""
        return _extract_user_id(self.client.api_key)
```

### Session Change Tracker

```python
@dataclass
class SessionState:
    """Tracks session state and detects changes after endpoint execution."""
    session: SessionData
    original_token: str
    original_user_id: str
    started_as_principal: bool

    @classmethod
    def for_principal(cls, session: SessionData) -> "SessionState":
        return cls(
            session=session,
            original_token=session.principal.access_token,
            original_user_id=session.principal.user_id,
            started_as_principal=True,
        )

    @classmethod
    def for_selected(cls, session: SessionData) -> "SessionState":
        active = session.delegated or session.principal
        return cls(
            session=session,
            original_token=active.access_token,
            original_user_id=active.user_id,
            started_as_principal=session.delegated is None,
        )

    def compute_updates(self, client: Client) -> SessionData | None:
        """Compare current client state with original, return updated session or None."""
        current_user_id = _extract_user_id(client.api_key)
        current_token = client.api_key
        principal_user_id = self.session.principal.user_id

        # Case 1: Ended on delegated user
        if current_user_id != principal_user_id:
            if current_user_id != self.original_user_id or current_token != self.original_token:
                return SessionData(
                    principal=self.session.principal,
                    delegated=TokenSet(
                        access_token=client.api_key,
                        refresh_token=client.refresh_token,
                        user_id=current_user_id,
                    ),
                )

        # Case 2: Ended on principal, but started on delegated (switch_back)
        elif not self.started_as_principal:
            new_principal = self._maybe_refresh_principal(client)
            return SessionData(principal=new_principal, delegated=None)

        # Case 3: Stayed on principal, maybe token refreshed
        elif current_token != self.original_token:
            return SessionData(
                principal=TokenSet(
                    access_token=client.api_key,
                    refresh_token=client.refresh_token,
                    user_id=principal_user_id,
                ),
                delegated=self.session.delegated,
            )

        return None  # No changes

    def _maybe_refresh_principal(self, client: Client) -> TokenSet:
        """Return updated principal tokens if they changed."""
        if client.api_key != self.session.principal.access_token:
            return TokenSet(
                access_token=client.api_key,
                refresh_token=client.refresh_token,
                user_id=self.session.principal.user_id,
            )
        return self.session.principal
```

### Clean Dependency Implementation

```python
from collections.abc import Generator


def _create_user_and_state(
    session: SessionData,
    use_delegated: bool,
) -> tuple[SweatStackUser, SessionState]:
    """Create user and state tracker from session data."""
    if use_delegated and session.delegated:
        tokens = session.delegated
    else:
        tokens = session.principal

    state = SessionState.for_selected(session) if use_delegated else SessionState.for_principal(session)

    client = Client(
        api_key=tokens.access_token,
        refresh_token=tokens.refresh_token,
        client_id=get_config().client_id,
        client_secret=get_config().client_secret.get_secret_value(),
    )

    return SweatStackUser(client=client), state


def _persist_if_changed(
    response: Response,
    user: SweatStackUser,
    state: SessionState,
) -> None:
    """Persist session changes if any occurred."""
    if updated := state.compute_updates(user.client):
        set_session_cookie(response, updated.to_dict())


def _require_user(
    request: Request,
    response: Response,
    *,
    use_delegated: bool,
) -> Generator[SweatStackUser, None, None]:
    """Core dependency logic for authenticated users."""
    session = SessionData.from_dict(decrypt_session(request))
    user, state = _create_user_and_state(session, use_delegated)

    yield user

    _persist_if_changed(response, user, state)


def _optional_user(
    request: Request,
    response: Response,
    *,
    use_delegated: bool,
) -> Generator[SweatStackUser | None, None, None]:
    """Core dependency logic for optional authentication."""
    session_cookie = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_cookie:
        yield None
        return

    try:
        session = SessionData.from_dict(decrypt_session(request))
    except (InvalidSession, ExpiredSession):
        yield None
        return

    user, state = _create_user_and_state(session, use_delegated)

    yield user

    _persist_if_changed(response, user, state)


# Concrete dependency functions (required by FastAPI's Depends)
def _require_authenticated_user(request: Request, response: Response):
    yield from _require_user(request, response, use_delegated=False)


def _require_selected_user(request: Request, response: Response):
    yield from _require_user(request, response, use_delegated=True)


def _optional_authenticated_user(request: Request, response: Response):
    yield from _optional_user(request, response, use_delegated=False)


def _optional_selected_user(request: Request, response: Response):
    yield from _optional_user(request, response, use_delegated=True)


# Public type aliases for FastAPI endpoints
AuthenticatedUser = Annotated[SweatStackUser, Depends(_require_authenticated_user)]
SelectedUser = Annotated[SweatStackUser, Depends(_require_selected_user)]
OptionalUser = Annotated[SweatStackUser | None, Depends(_optional_authenticated_user)]
OptionalSelectedUser = Annotated[SweatStackUser | None, Depends(_optional_selected_user)]
```

### Helper Utilities

```python
import base64
import json


def _extract_user_id(jwt_token: str) -> str:
    """Extract 'sub' (user ID) from JWT without validation.

    We don't validate the signature here because the token was already
    validated by the API when it was issued.
    """
    try:
        payload_b64 = jwt_token.split(".")[1]
        # Add padding if needed
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        return payload["sub"]
    except (IndexError, KeyError, json.JSONDecodeError) as e:
        raise InvalidTokenError("Could not extract user ID from token") from e
```

### Why This Architecture?

1. **Single source of truth**: `_user_dependency` contains all shared logic
2. **Type-safe data models**: `TokenSet` and `SessionData` prevent dict key typos
3. **Separated concerns**: `SessionState` handles change detection, dependencies handle HTTP
4. **Testable**: Each class can be unit tested in isolation
5. **Immutable where possible**: `TokenSet` is frozen, preventing accidental mutation
6. **Clear public API**: Only the `Annotated` types are exported
7. **Private implementation**: Functions prefixed with `_` are internal; only type aliases are public

---

## Design Decisions

| Question | Decision |
|----------|----------|
| Opt-in vs always available | Always available, transparent if not used |
| HTTP method for routes | POST only (security) |
| OptionalUser behavior | Returns principal (backwards compatible) |
| New optional selected type | `OptionalSelectedUser` |
| User names vs IDs | IDs only for now |
| Access revoked while selected | Let it fail naturally (API returns 403) |
| Default redirect | Referrer if available, then `?next=`, then `/` |
| Naming | `select_user()` / `select_self()` |
| CSRF protection | Out of scope — application developer's responsibility |
| Cookie updates | Only when changed (avoids unnecessary Set-Cookie headers) |
| Permission denied on select routes | Return 403 directly |
