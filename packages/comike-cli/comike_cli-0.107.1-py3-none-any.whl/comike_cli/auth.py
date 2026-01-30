"""OAuth2.0 authentication for Circle.ms API."""

import json
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import httpx

AUTH_URL = "https://auth1.circle.ms/OAuth2/"
TOKEN_URL = "https://auth1.circle.ms/OAuth2/Token"
REDIRECT_URI = "https://auth1.circle.ms/OAuth2/Blank"
SCOPES = "circle_read favorite_read favorite_write user_info"


@dataclass
class Token:
    """OAuth2 token."""

    access_token: str
    refresh_token: str
    expires_at: datetime

    def is_expired(self) -> bool:
        """Check if token is expired."""
        return datetime.now() >= self.expires_at

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.expires_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Token":
        """Create from dictionary."""
        return cls(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.fromisoformat(data["expires_at"]),
        )


class AuthManager:
    """Manages OAuth2 authentication."""

    def __init__(self, client_id: str, client_secret: str, token_file: Path):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_file = token_file
        self._token: Token | None = None

    def get_token(self) -> Token:
        """Get valid access token, refreshing if necessary."""
        if self._token is None:
            self._token = self._load_token()

        if self._token is None:
            self._token = self._authorize()
            self._save_token(self._token)
        elif self._token.is_expired():
            self._token = self._refresh_token(self._token.refresh_token)
            self._save_token(self._token)

        return self._token

    def _load_token(self) -> Token | None:
        """Load token from file."""
        if not self.token_file.exists():
            return None
        try:
            data = json.loads(self.token_file.read_text())
            return Token.from_dict(data)
        except (json.JSONDecodeError, KeyError):
            return None

    def _save_token(self, token: Token) -> None:
        """Save token to file."""
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(json.dumps(token.to_dict(), indent=2))

    def _authorize(self) -> Token:
        """Perform OAuth2 authorization flow."""
        import secrets

        state = secrets.token_urlsafe(16)

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": REDIRECT_URI,
            "state": state,
            "scope": SCOPES,
        }
        auth_url = f"{AUTH_URL}?{urlencode(params)}"

        print("ブラウザで認証ページを開きます...")
        print("認証後、リダイレクト先のURLをコピーしてください。")
        print()
        webbrowser.open(auth_url)

        # Get redirect URL from user
        redirect_url = input("リダイレクト先URL: ").strip()

        # Parse authorization code from URL
        parsed = urlparse(redirect_url)
        query = parse_qs(parsed.query)

        # Check for error response
        if "error" in query:
            error = query.get("error", ["unknown"])[0]
            error_desc = query.get("error_description", [""])[0]
            raise RuntimeError(f"認証エラー: {error} - {error_desc}")

        # Verify state
        if query.get("state", [None])[0] != state:
            raise RuntimeError("stateパラメータが一致しません")

        auth_code = query.get("code", [None])[0]
        if not auth_code:
            raise RuntimeError("認証コードを取得できませんでした")

        return self._exchange_code(auth_code)

    def _exchange_code(self, code: str) -> Token:
        """Exchange authorization code for token."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = httpx.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return self._parse_token_response(response.json())

    def _refresh_token(self, refresh_token: str) -> Token:
        """Refresh access token."""
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = httpx.post(
            TOKEN_URL,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return self._parse_token_response(response.json())

    def _parse_token_response(self, data: dict) -> Token:
        """Parse token response."""
        expires_in = int(data.get("expires_in", 86400))
        return Token(
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.now() + timedelta(seconds=expires_in),
        )
