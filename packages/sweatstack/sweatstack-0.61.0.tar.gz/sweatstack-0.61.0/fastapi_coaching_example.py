"""Example FastAPI app demonstrating user switching for coaching platforms.

Run with:
    uv run fastapi dev fastapi_coaching_example.py

Required environment variables:
    SWEATSTACK_CLIENT_ID
    SWEATSTACK_CLIENT_SECRET
    SWEATSTACK_SESSION_SECRET
    APP_URL (e.g., http://localhost:8000)
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from sweatstack.fastapi import (
    AuthenticatedUser,
    OptionalSelectedUser,
    OptionalUser,
    configure,
    instrument,
    urls,
)

configure(
    client_id="1da141eeffa54c4d",
    client_secret="vgwMFP6uTQa3K5bBc1mDqU33xnHVwhyqVq-NLacopD0",
    session_secret="5YviwYhzDdmzsqbcEIP0QXzoiehIy8lqBWLtzaeBU8Q=",
    app_url="http://localhost:8000",
)

app = FastAPI(title="SweatStack Coaching Demo")
instrument(app)


@app.get("/", response_class=HTMLResponse)
def home(user: OptionalSelectedUser, principal: OptionalUser):
    """Home page with dashboard."""
    if not user:
        return f"""
        <h1>Coaching Demo</h1>
        <a href="{urls.login()}">Login with SweatStack</a>
        """

    activities = user.client.get_activities(limit=5)

    activity_list = "".join(
        f"<li>{a.sport.display_name()} - {a.start_local.strftime('%Y-%m-%d')}</li>"
        for a in activities
    ) or "<li>No activities</li>"

    viewing_as = ""
    back_link = ""
    if principal and user.user_id != principal.user_id:
        viewing_as = f"<p><strong>Viewing as:</strong> {user.user_id}</p>"
        back_link = f"""
        <form method="post" action="{urls.select_self()}" style="display:inline">
            <button>Back to my data</button>
        </form> |
        """

    return f"""
    <h1>Dashboard</h1>
    {viewing_as}
    <p>{back_link}<a href="/select-user">Select user</a> |
    <form method="post" action="{urls.logout()}" style="display:inline">
        <button>Logout</button>
    </form></p>
    <h2>Recent Activities</h2>
    <ul>{activity_list}</ul>
    """


@app.get("/select-user", response_class=HTMLResponse)
def select_user(user: AuthenticatedUser):
    """Select a user to view."""
    accessible = user.client.get_users()

    user_list = ""
    for u in accessible:
        if u.id == user.user_id:
            user_list += f"<li><strong>{u.display_name or u.id}</strong> (you)</li>"
        else:
            user_list += f"""
            <li>
                {u.display_name or u.id}
                <form method="post" action="{urls.select_user(u.id, next='/')}" style="display:inline">
                    <button>Select</button>
                </form>
            </li>
            """

    return f"""
    <h1>Select User</h1>
    <p><a href="/">Back</a></p>
    <ul>{user_list}</ul>
    """
