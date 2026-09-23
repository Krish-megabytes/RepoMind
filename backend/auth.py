"""GitHub OAuth authentication helpers for RepoMind.

Implements:
- Login redirect to GitHub OAuth authorize endpoint.
- Token exchange callback.
- Current‑user helper that validates a token and returns user info.
"""

from dataclasses import dataclass
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from .config import settings

router = APIRouter(prefix="/auth", tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_API = "https://api.github.com/user"


@dataclass
class User:
    id: str
    login: str
    avatar_url: str


# In‑memory session store (swap for a real DB / JWT in production)
_sessions: dict[str, User] = {}


@router.get("/login")
async def login():
    """Redirect the user to GitHub for authorization."""
    return RedirectResponse(
        f"{GITHUB_AUTHORIZE_URL}?client_id={settings.GITHUB_CLIENT_ID}"
        f"&redirect_uri={settings.GITHUB_REDIRECT_URI}&scope=read:user"
    )


@router.get("/callback")
async def callback(code: str):
    """Exchange the authorization code for an access token and fetch user info."""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": str(settings.GITHUB_REDIRECT_URI),
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="GitHub token exchange failed")
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token returned")

        user_resp = await client.get(
            GITHUB_USER_API,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to fetch GitHub user")
        user_data = user_resp.json()

    user = User(
        id=str(user_data["id"]),
        login=user_data["login"],
        avatar_url=user_data.get("avatar_url", ""),
    )
    _sessions[access_token] = user
    # In production, set an HTTP‑only cookie instead of returning the token directly
    return {"access_token": access_token, "user": user.__dict__}


async def get_current_user(token: str) -> User | None:
    """Validate a token and return the associated user, or None."""
    if token in _sessions:
        return _sessions[token]
    # Attempt a live lookup against GitHub
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GITHUB_USER_API,
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        user = User(
            id=str(data["id"]),
            login=data["login"],
            avatar_url=data.get("avatar_url", ""),
        )
        _sessions[token] = user
        return user
