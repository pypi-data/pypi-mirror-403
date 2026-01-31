# FastAPI Integration

Add SweatStack authentication to your FastAPI app in minutes. Your users authenticate with SweatStack, and you get a ready-to-use API client for each request.

## Installation

```bash
pip install 'sweatstack[fastapi]'
```

## Prerequisites

Before you start, you'll need OAuth credentials from SweatStack:

1. Go to [SweatStack Developer Settings](https://app.sweatstack.no/settings/developer)
2. Register a new application
3. Set the redirect URI to `http://localhost:8000/auth/sweatstack/callback`
4. Note your **Client ID** and **Client Secret**

!!! tip "Redirect URI"
    The redirect URI must match exactly. For local development, use `http://localhost:8000/auth/sweatstack/callback`. Update this when deploying to production.

## Quickstart

Create a file called `app.py`:

```python
from fastapi import FastAPI
from sweatstack.fastapi import configure, instrument, AuthenticatedUser

configure()

app = FastAPI()
instrument(app)


@app.get("/")
def home(user: AuthenticatedUser):
    return {"message": f"Welcome, {user.user_id}!"}


@app.get("/activities")
def activities(user: AuthenticatedUser):
    return user.client.get_activities(limit=10)
```

That's the entire app. Let's run it.

## Set Environment Variables

The plugin reads configuration from environment variables:

```bash
export SWEATSTACK_CLIENT_ID="your-client-id"
export SWEATSTACK_CLIENT_SECRET="your-client-secret"
export SWEATSTACK_SESSION_SECRET="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
export APP_URL="http://localhost:8000"
```

!!! note "Session Secret"
    The session secret encrypts tokens stored in cookies. Generate a new one for each environment. Never commit it to version control.

## Run Your App

```bash
fastapi dev app.py
```

Open [http://localhost:8000](http://localhost:8000) in your browser. You'll be redirected to SweatStack to log in, then back to your app with full API access.

---

## How It Works

The plugin adds three routes to your app:

| Route | Description |
|-------|-------------|
| `GET /auth/sweatstack/login` | Redirects to SweatStack OAuth |
| `GET /auth/sweatstack/callback` | Handles the OAuth callback |
| `POST /auth/sweatstack/logout` | Clears the session |

When a user visits a protected route:

1. If not logged in → redirected to `/auth/sweatstack/login`
2. If logged in → your route handler receives a `SweatStackUser` with:
   - `user.user_id` — the authenticated user's ID
   - `user.client` — a configured API client for that user

Tokens are stored in encrypted, httponly cookies. No database required.

---

## Protecting Routes

### Require Authentication

Use `AuthenticatedUser` for routes that require a logged-in user:

```python
from sweatstack.fastapi import AuthenticatedUser

@app.get("/dashboard")
def dashboard(user: AuthenticatedUser):
    return user.client.get_activities()
```

If the user isn't logged in, they're automatically redirected to the login page.

### Optional Authentication

Use `OptionalUser` for routes that work with or without authentication:

```python
from sweatstack.fastapi import OptionalUser

@app.get("/")
def home(user: OptionalUser):
    if user:
        return {"message": f"Hello, {user.user_id}!"}
    return {"message": "Hello, guest! Please log in."}
```

---

## Building Login/Logout UI

Use the `urls` helper to build login and logout links:

```python
from fastapi.responses import HTMLResponse
from sweatstack.fastapi import AuthenticatedUser, OptionalUser, urls

@app.get("/")
def home(user: OptionalUser):
    if user:
        return HTMLResponse(f"""
            <p>Welcome, {user.user_id}!</p>
            <form method="POST" action="{urls.logout()}">
                <button type="submit">Logout</button>
            </form>
        """)
    return HTMLResponse(f"""
        <p>Please log in to continue.</p>
        <a href="{urls.login()}">Login with SweatStack</a>
    """)
```

The `urls` helper provides:

- `urls.login()` — returns `/auth/sweatstack/login`
- `urls.login(next="/dashboard")` — login with redirect after auth
- `urls.logout()` — returns `/auth/sweatstack/logout`

---

## Configuration Reference

All parameters can be passed to `configure()` or set via environment variables:

```python
from sweatstack.fastapi import configure

configure(
    # Required (or use environment variables)
    client_id="...",                   # env: SWEATSTACK_CLIENT_ID
    client_secret="...",               # env: SWEATSTACK_CLIENT_SECRET
    app_url="http://localhost:8000",   # env: APP_URL
    session_secret="...",              # env: SWEATSTACK_SESSION_SECRET

    # Optional
    scopes=["profile", "data:read"],   # OAuth scopes to request
    cookie_max_age=86400,              # Session lifetime in seconds (default: 24h)
    auth_route_prefix="/auth/sweatstack",  # Prefix for auth routes
    redirect_unauthenticated=True,     # Redirect to login vs return 401
)
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SWEATSTACK_CLIENT_ID` | Your OAuth client ID |
| `SWEATSTACK_CLIENT_SECRET` | Your OAuth client secret |
| `SWEATSTACK_SESSION_SECRET` | Fernet key for cookie encryption |
| `APP_URL` | Base URL of your app (e.g., `http://localhost:8000`) |

### Generating a Session Secret

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### Key Rotation

For zero-downtime secret rotation, pass a list of keys. The first key encrypts new sessions; all keys are tried for decryption:

```python
configure(
    session_secret=[
        os.environ["SESSION_SECRET_NEW"],
        os.environ["SESSION_SECRET_OLD"],
    ],
)
```

---

## Security

The plugin follows security best practices:

- **Encrypted cookies** — Tokens are encrypted with Fernet (AES-128-CBC + HMAC)
- **HttpOnly** — Cookies are not accessible via JavaScript
- **Secure flag** — Automatically enabled for HTTPS URLs
- **SameSite=Lax** — Protection against CSRF attacks
- **State parameter** — OAuth state validated to prevent CSRF
- **Redirect validation** — Only relative paths allowed in `?next=` parameter

---

## Example: Complete App

Here's a complete example with multiple routes:

```python
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from sweatstack.fastapi import (
    configure, instrument, AuthenticatedUser, OptionalUser, urls
)

configure()

app = FastAPI(title="My SweatStack App")
instrument(app)


@app.get("/")
def home(user: OptionalUser):
    if user:
        return HTMLResponse(f"""
            <h1>Welcome back!</h1>
            <p>User ID: {user.user_id}</p>
            <ul>
                <li><a href="/activities">My Activities</a></li>
                <li><a href="/profile">My Profile</a></li>
            </ul>
            <form method="POST" action="{urls.logout()}">
                <button type="submit">Logout</button>
            </form>
        """)
    return HTMLResponse(f"""
        <h1>Welcome!</h1>
        <p><a href="{urls.login()}">Login with SweatStack</a></p>
    """)


@app.get("/activities")
def activities(user: AuthenticatedUser):
    return user.client.get_activities(limit=10)


@app.get("/profile")
def profile(user: AuthenticatedUser):
    return user.client.get_userinfo()
```

---

## Next Steps

- Explore the [SweatStack API Reference](/reference/) to see what data you can access
- Learn about [OAuth2 concepts](/learn/oauth2-openid/) for deeper understanding
- Check out the [Python client documentation](/learn/python-client/) for all available methods
