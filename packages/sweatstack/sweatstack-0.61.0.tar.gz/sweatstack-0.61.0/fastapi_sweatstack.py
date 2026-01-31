# /// script
# dependencies = [
#   "fastapi[dev]",
#   "sweatstack[fastapi] @ file://.",
# ]
# ///
import os

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from sweatstack.fastapi import (
    AuthenticatedUser, configure, instrument, OptionalUser, urls,
)


# Set environment variables for testing (in production, set these externally)
os.environ.setdefault("SWEATSTACK_CLIENT_ID", "1da141eeffa54c4d")
os.environ.setdefault("SWEATSTACK_CLIENT_SECRET", "vgwMFP6uTQa3K5bBc1mDqU33xnHVwhyqVq-NLacopD0")
os.environ.setdefault("SWEATSTACK_SESSION_SECRET", "5YviwYhzDdmzsqbcEIP0QXzoiehIy8lqBWLtzaeBU8Q=")
os.environ.setdefault("APP_URL", "http://localhost:8000")


configure()

app = FastAPI(title="SweatLab")

instrument(app)


@app.get("/")
def home(user: OptionalUser):
    """Home page - redirects to login if not authenticated."""
    if not user:
        return RedirectResponse("/login")
    return user
    return HTMLResponse(
        f"<h1>Welcome to SweatLab!</h1>"
        f"<p>Logged in as user: {user.user_id}</p>"
        f"<p>Logged in as user: {user.client}</p>"
        "<a href='/activities'>activities</a><br>"
        "<a href='/profile'>profile</a><br>"
        f'<form method="POST" action="{urls.logout()}">'
        f'<button type="submit">Logout</button>'
        f'</form>'
    )

@app.get("/login")
def login_page():
    """Login page with link to SweatStack OAuth."""
    return HTMLResponse(
        f"<a href='{urls.login()}'>login with SweatStack</a>"
    )


@app.get("/activities")
def get_activities(user: AuthenticatedUser):
    """Fetch the authenticated user's activities."""
    return user.client.get_activities()


@app.get("/profile")
def get_profile(user: AuthenticatedUser):
    """Get the authenticated user's profile information."""
    return user.client.get_userinfo()


