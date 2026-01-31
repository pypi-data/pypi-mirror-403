"""Example FastAPI app with SweatStack authentication.

Demonstrates both authenticated and selected user patterns for
coaching/delegation scenarios.
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from sweatstack.fastapi import (
    AuthenticatedUser,
    OptionalUser,
    SelectedUser,
    configure,
    instrument,
    urls,
)

configure()  # Uses SWEATSTACK_* environment variables

app = FastAPI()
instrument(app)


@app.get("/", response_class=HTMLResponse)
def home(user: OptionalUser):
    """Public home page with login state awareness."""
    if user:
        return f"""
        <h1>Welcome, {user.user_id}!</h1>
        <p><a href="/dashboard">Go to dashboard</a></p>
        <form method="post" action="{urls.logout()}">
            <button>Logout</button>
        </form>
        """
    return f"""
    <h1>Welcome to SweatStack Demo</h1>
    <p><a href="{urls.login(next='/dashboard')}">Login with SweatStack</a></p>
    """


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(user: AuthenticatedUser):
    """Dashboard showing the principal user and their accessible users."""
    # Get users the principal can access (for coaching scenarios)
    accessible_users = user.client.get_users()

    user_links = "".join(
        f"""
        <li>
            {u.display_name or u.id}
            <form method="post" action="{urls.select_user(u.id, next='/activities')}" style="display:inline">
                <button>View as</button>
            </form>
        </li>
        """
        for u in accessible_users
        if u.id != user.user_id
    )

    return f"""
    <h1>Dashboard</h1>
    <p>Logged in as: {user.user_id}</p>
    <h2>Accessible Users</h2>
    <ul>{user_links or "<li>No other users</li>"}</ul>
    <p><a href="/activities">View my activities</a></p>
    """


@app.get("/activities", response_class=HTMLResponse)
def activities(user: SelectedUser, principal: AuthenticatedUser):
    """Activities page showing the selected user's data."""
    # SelectedUser returns delegated user if selected, otherwise principal
    activities_list = user.client.get_activities(limit=10)

    activities_html = "".join(
        f"<li>{a.sport} - {a.start_local.strftime('%Y-%m-%d')}</li>" for a in activities_list
    )

    # Show "back to my view" if viewing as someone else
    if user.user_id != principal.user_id:
        back_button = f"""
        <form method="post" action="{urls.select_self(next='/activities')}">
            <button>Back to my activities</button>
        </form>
        """
    else:
        back_button = ""

    return f"""
    <h1>Activities for {user.user_id}</h1>
    {back_button}
    <ul>{activities_html or "<li>No activities</li>"}</ul>
    <p><a href="/dashboard">Back to dashboard</a></p>
    """
