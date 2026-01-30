"""Circle.ms WebCatalog API client."""

from pathlib import Path
from typing import Any

import httpx

from .auth import AuthManager
from .database import CatalogDatabase

API_BASE = "https://api1.circle.ms"


class CircleMsClient:
    """Client for Circle.ms WebCatalog API."""

    def __init__(self, auth_manager: AuthManager, data_dir: Path | None = None):
        self.auth = auth_manager
        self._client = httpx.Client(timeout=30.0)
        self._data_dir = data_dir or Path.home() / ".comike_cli" / "data"
        self._db = CatalogDatabase(self._data_dir)
        self._current_event_id: int | None = None

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        data: dict | None = None,
    ) -> dict[str, Any]:
        """Make authenticated API request."""
        token = self.auth.get_token()
        headers = {"Authorization": f"Bearer {token.access_token}"}

        url = f"{API_BASE}{path}"

        if method == "GET":
            response = self._client.get(url, params=params, headers=headers)
        elif method == "POST":
            response = self._client.post(url, data=data, headers=headers)
        elif method == "PUT":
            response = self._client.put(url, data=data, headers=headers)
        elif method == "DELETE":
            response = self._client.delete(url, params=params, headers=headers)
        else:
            raise ValueError(f"Unsupported method: {method}")

        response.raise_for_status()
        return response.json()

    def get_event_list(self) -> dict[str, Any]:
        """Get list of events."""
        return self._request("GET", "/WebCatalog/GetEventList/")

    def search_circles(
        self,
        event_id: int | None = None,
        circle_name: str | None = None,
        genre: int | None = None,
        floor: int | None = None,
        sort: int = 1,
        page: int = 1,
    ) -> dict[str, Any]:
        """Search circles."""
        params = {"sort": sort, "page": page}
        if event_id:
            params["event_id"] = event_id
        if circle_name:
            params["circle_name"] = circle_name
        if genre:
            params["genre"] = genre
        if floor:
            params["floor"] = floor

        return self._request("GET", "/WebCatalog/QueryCircle/", params=params)

    def get_circle(self, wcid: int) -> dict[str, Any]:
        """Get circle details."""
        return self._request("GET", "/WebCatalog/GetCircle/", params={"wcid": wcid})

    def search_books(
        self,
        event_id: int | None = None,
        circle_name: str | None = None,
        work_name: str | None = None,
        page: int = 1,
    ) -> dict[str, Any]:
        """Search books/works."""
        params = {"page": page}
        if event_id:
            params["event_id"] = event_id
        if circle_name:
            params["circle_name"] = circle_name
        if work_name:
            params["work_name"] = work_name

        return self._request("GET", "/WebCatalog/QueryBook/", params=params)

    def get_user_info(self) -> dict[str, Any]:
        """Get user information."""
        return self._request("POST", "/User/Info/")

    def get_user_circles(self) -> dict[str, Any]:
        """Get circles owned by the user."""
        return self._request("POST", "/User/Circles/")

    def get_favorite_circles(
        self,
        event_id: int | None = None,
        page: int = 1,
    ) -> dict[str, Any]:
        """Get favorite circles."""
        params = {"page": page}
        if event_id:
            params["event_id"] = event_id

        return self._request("GET", "/Readers/FavoriteCircles/", params=params)

    def add_favorite(
        self,
        wcid: int,
        color: int = 1,
        memo: str = "",
        free: str = "",
    ) -> dict[str, Any]:
        """Add circle to favorites."""
        data = {
            "wcid": wcid,
            "color": color,
            "memo": memo,
            "free": free,
        }
        return self._request("POST", "/Readers/Favorite", data=data)

    def update_favorite(
        self,
        wcid: int,
        color: int,
        memo: str,
        free: str = "",
    ) -> dict[str, Any]:
        """Update favorite circle info."""
        data = {
            "wcid": wcid,
            "color": color,
            "memo": memo,
            "free": free,
        }
        return self._request("PUT", "/Readers/Favorite", data=data)

    def remove_favorite(self, wcid: int) -> dict[str, Any]:
        """Remove circle from favorites."""
        return self._request("DELETE", "/Readers/Favorite", params={"wcid": wcid})

    def get_favorite_works(
        self,
        event_id: int | None = None,
        circle_name: str | None = None,
        work_name: str | None = None,
        genre: int | None = None,
        floor: int | None = None,
        page: int = 1,
    ) -> dict[str, Any]:
        """Get works from favorite circles."""
        params = {"page": page}
        if event_id:
            params["event_id"] = event_id
        if circle_name:
            params["circle_name"] = circle_name
        if work_name:
            params["work_name"] = work_name
        if genre:
            params["genre"] = genre
        if floor:
            params["floor"] = floor

        return self._request("GET", "/Readers/FavoriteWorks/", params=params)

    def ensure_database(self, event_id: int | None = None) -> int:
        """Ensure local database is downloaded for the event."""
        if event_id is None:
            # Get latest event
            events = self.get_event_list()
            event_id = events.get("response", {}).get("LatestEventId")
            if not event_id:
                raise RuntimeError("イベントIDを取得できませんでした")

        if self._current_event_id == event_id:
            return event_id

        # Get database URL
        base_data = self._request("GET", "/CatalogBase/All/", params={"event_id": event_id})
        urls = base_data.get("response", {}).get("url", {})

        # Prefer SQLite3 zip (smaller download)
        db_url = (
            urls.get("textdb_sqlite3_zip_url_ssl")
            or urls.get("textdb_sqlite3_url_ssl")
            or urls.get("textdb_sqlite3_zip_url")
            or urls.get("textdb_sqlite3_url")
        )

        if not db_url:
            raise RuntimeError("データベースURLを取得できませんでした")

        self._db.download(db_url, event_id)
        self._db.open(event_id)
        self._current_event_id = event_id
        return event_id

    def get_placement(self, wcid: int) -> dict | None:
        """Get circle placement info."""
        if not self._current_event_id:
            self.ensure_database()
        return self._db.get_placement_by_wcid(wcid)

    def search_circles_local(
        self,
        name: str | None = None,
        block: str | None = None,
        day: int | None = None,
        genre: str | None = None,
        space_from: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Search circles in local database with placement info.

        Block name matching:
        - Hiragana/Katakana are distinct (あ ≠ ア)
        - English is case/width insensitive (A = a = Ａ)
        """
        if not self._current_event_id:
            self.ensure_database()
        return self._db.search_circles_with_placement(
            name=name,
            block=block,
            day=day,
            genre=genre,
            space_from=space_from,
            limit=limit,
            offset=offset,
        )

    def get_maps(self) -> list[dict]:
        """Get all hall maps."""
        if not self._current_event_id:
            self.ensure_database()
        return self._db.get_maps()

    def get_genres(self, day: int | None = None) -> list[dict]:
        """Get genre list."""
        if not self._current_event_id:
            self.ensure_database()
        return self._db.get_genres(day=day)

    def get_circle_map(self, wcid: int) -> dict:
        """Get circle position on hall map with ASCII visualization."""
        if not self._current_event_id:
            self.ensure_database()

        pos = self._db.get_circle_map_position(wcid)
        if not pos:
            return {"error": "サークルが見つかりません", "wcid": wcid}

        # Render the map with the circle highlighted
        map_art = self._db.render_hall_map(
            map_id=pos["map_id"],
            highlight_x=pos["xpos"],
            highlight_y=pos["ypos"],
        )

        return {
            "circle_name": pos["circle_name"],
            "placement": f"{pos['day']}日目 {pos['block']}{pos['space']}",
            "hall": pos["map_name"],
            "map_art": map_art,
        }
