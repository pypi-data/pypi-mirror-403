"""Local SQLite database for circle placement information."""

import sqlite3
import zipfile
from io import BytesIO
from pathlib import Path

import httpx


def normalize_block_for_search(block: str) -> str:
    """Normalize block name for search comparison.

    - Hiragana/Katakana: Keep distinct (あ ≠ ア)
    - English: Case-insensitive, full/half-width insensitive (A = a = Ａ = ａ)
    """
    # Convert full-width alphanumeric to half-width
    result = ""
    for char in block:
        code = ord(char)
        # Full-width uppercase A-Z (U+FF21 - U+FF3A) -> half-width a-z
        if 0xFF21 <= code <= 0xFF3A:
            result += chr(code - 0xFF21 + ord("a"))
        # Full-width lowercase a-z (U+FF41 - U+FF5A) -> half-width a-z
        elif 0xFF41 <= code <= 0xFF5A:
            result += chr(code - 0xFF41 + ord("a"))
        # Half-width uppercase A-Z -> lowercase a-z
        elif ord("A") <= code <= ord("Z"):
            result += chr(code - ord("A") + ord("a"))
        # Keep everything else as-is (including hiragana/katakana distinction)
        else:
            result += char
    return result


def blocks_match(block1: str, block2: str) -> bool:
    """Check if two block names match with normalization rules."""
    return normalize_block_for_search(block1) == normalize_block_for_search(block2)


class CatalogDatabase:
    """Manages local catalog database with placement info."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._event_id: int | None = None

    def _get_db_path(self, event_id: int) -> Path:
        return self.data_dir / f"catalog_{event_id}.db"

    def download(self, db_url: str, event_id: int) -> None:
        """Download and extract database from URL."""
        db_path = self._get_db_path(event_id)

        if db_path.exists():
            # Already downloaded
            return

        print("データベースをダウンロード中...")
        response = httpx.get(db_url, timeout=120.0, follow_redirects=True)
        response.raise_for_status()

        content = response.content

        # Check if it's a zip file
        if db_url.endswith(".zip") or content[:2] == b"PK":
            with zipfile.ZipFile(BytesIO(content)) as zf:
                # Find the .db or .sqlite file
                for name in zf.namelist():
                    if name.endswith((".db", ".sqlite", ".sqlite3")):
                        with zf.open(name) as f:
                            db_path.write_bytes(f.read())
                        break
                else:
                    # Just extract first file
                    first_file = zf.namelist()[0]
                    with zf.open(first_file) as f:
                        db_path.write_bytes(f.read())
        else:
            # Direct database file
            db_path.write_bytes(content)

        print(f"データベースを保存しました: {db_path}")

    def open(self, event_id: int) -> None:
        """Open database connection."""
        if self._conn and self._event_id == event_id:
            return

        self.close()
        db_path = self._get_db_path(event_id)
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._event_id = event_id

    def close(self) -> None:
        """Close database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._event_id = None

    def get_placement(self, update_id: int) -> dict | None:
        """Get circle placement info by updateId."""
        if not self._conn:
            return None

        cursor = self._conn.execute(
            """
            SELECT
                c.day,
                c.blockId,
                c.spaceNo,
                c.spaceNoSub,
                b.name as blockName
            FROM ComiketCircleWC c
            LEFT JOIN ComiketBlockWC b ON c.comiketNo = b.comiketNo AND c.blockId = b.id
            WHERE c.updateId = ?
            """,
            (update_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        space_sub = "a" if row["spaceNoSub"] == 0 else "b"
        return {
            "day": row["day"],
            "block": row["blockName"] or f"Block{row['blockId']}",
            "space": f"{row['spaceNo']:02d}{space_sub}",
            "full": f"{row['day']}日目 {row['blockName']}{row['spaceNo']:02d}{space_sub}",
        }

    def get_placement_by_wcid(self, wcid: int) -> dict | None:
        """Get circle placement info by wcid."""
        if not self._conn:
            return None

        # First try to find via ComiketCircleExtend
        cursor = self._conn.execute(
            """
            SELECT c.updateId
            FROM ComiketCircleExtend e
            JOIN ComiketCircleWC c ON e.comiketNo = c.comiketNo AND e.id = c.id
            WHERE e.WCId = ?
            """,
            (wcid,),
        )
        row = cursor.fetchone()
        if row:
            return self.get_placement(row["updateId"])

        return None

    def search_circles_with_placement(
        self,
        name: str | None = None,
        block: str | None = None,
        day: int | None = None,
        genre: str | None = None,
        space_from: int | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        """Search circles with placement info.

        Block name matching rules:
        - Hiragana/Katakana are distinct (あ ≠ ア)
        - English is case/width insensitive (A = a = Ａ)

        Args:
            space_from: Start from this space number (e.g., 40 for 40番以降)
            offset: Skip first N results (for pagination)

        Returns:
            dict with 'results', 'total', 'limit', 'offset', 'has_more'
        """
        if not self._conn:
            return {"results": [], "total": 0, "limit": limit, "offset": offset, "has_more": False}

        # Build WHERE clause
        where_clauses = ["1=1"]
        params: list = []

        if name:
            where_clauses.append("(c.circleName LIKE ? OR c.circleKana LIKE ?)")
            params.extend([f"%{name}%", f"%{name}%"])

        if day:
            where_clauses.append("c.day = ?")
            params.append(day)

        if genre:
            where_clauses.append("g.name LIKE ?")
            params.append(f"%{genre}%")

        if space_from is not None:
            where_clauses.append("c.spaceNo >= ?")
            params.append(space_from)

        # Block filter - need special handling for normalization
        block_params: list = []
        if block:
            # Get all matching block names from DB
            normalized_input = normalize_block_for_search(block)
            block_cursor = self._conn.execute("SELECT DISTINCT name FROM ComiketBlockWC")
            matching_blocks = [
                row["name"]
                for row in block_cursor
                if normalize_block_for_search(row["name"]) == normalized_input
            ]
            if matching_blocks:
                placeholders = ",".join("?" * len(matching_blocks))
                where_clauses.append(f"b.name IN ({placeholders})")
                block_params = matching_blocks
            else:
                # No matching blocks, return empty
                return {
                    "results": [],
                    "total": 0,
                    "limit": limit,
                    "has_more": False,
                }

        where_sql = " AND ".join(where_clauses)
        all_params = params + block_params

        # Get total count first
        count_query = f"""
            SELECT COUNT(*) as cnt
            FROM ComiketCircleWC c
            LEFT JOIN ComiketBlockWC b ON c.comiketNo = b.comiketNo AND c.blockId = b.id
            LEFT JOIN ComiketGenreWC g ON c.comiketNo = g.comiketNo AND c.genreId = g.id
            WHERE {where_sql}
        """
        cursor = self._conn.execute(count_query, all_params)
        total_count = cursor.fetchone()["cnt"]

        # Get results
        query = f"""
            SELECT
                c.id,
                c.circleName,
                c.circleKana,
                c.penName,
                c.day,
                c.blockId,
                c.spaceNo,
                c.spaceNoSub,
                c.updateId,
                c.genreId,
                b.name as blockName,
                g.name as genreName,
                e.WCId as wcid
            FROM ComiketCircleWC c
            LEFT JOIN ComiketBlockWC b ON c.comiketNo = b.comiketNo AND c.blockId = b.id
            LEFT JOIN ComiketGenreWC g ON c.comiketNo = g.comiketNo AND c.genreId = g.id
            LEFT JOIN ComiketCircleExtend e ON c.comiketNo = e.comiketNo AND c.id = e.id
            WHERE {where_sql}
            ORDER BY c.day, c.blockId, c.spaceNo
            LIMIT ? OFFSET ?
        """
        cursor = self._conn.execute(query, all_params + [limit, offset])

        results = []
        for row in cursor:
            block_name = row["blockName"] or f"Block{row['blockId']}"

            space_sub = "a" if row["spaceNoSub"] == 0 else "b"
            results.append(
                {
                    "wcid": row["wcid"],
                    "name": row["circleName"],
                    "name_kana": row["circleKana"],
                    "pen_name": row["penName"],
                    "day": row["day"],
                    "block": block_name,
                    "space": f"{row['spaceNo']:02d}{space_sub}",
                    "placement": f"{row['day']}日目 {block_name}{row['spaceNo']:02d}{space_sub}",
                    "genre": row["genreName"],
                    "update_id": row["updateId"],
                }
            )

            if len(results) >= limit:
                break

        return {
            "results": results,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": (offset + len(results)) < total_count,
        }

    def get_genres(self, day: int | None = None) -> list[dict]:
        """Get genre list.

        Args:
            day: Filter by day (1, 2, ...). None returns all genres.
        """
        if not self._conn:
            return []

        if day is not None:
            # Include day-specific genres and day=0 (any day) genres
            cursor = self._conn.execute(
                """
                SELECT id, name, code, day
                FROM ComiketGenreWC
                WHERE day = ? OR day = 0
                ORDER BY code
                """,
                (day,),
            )
        else:
            cursor = self._conn.execute(
                "SELECT id, name, code, day FROM ComiketGenreWC ORDER BY day, code"
            )

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "code": row["code"],
                "day": row["day"],
            }
            for row in cursor
        ]

    def get_maps(self) -> list[dict]:
        """Get all maps with their coordinate ranges."""
        if not self._conn:
            return []

        cursor = self._conn.execute("""
            SELECT
                m.id,
                m.name,
                m.filename,
                MIN(l.xpos) as min_x,
                MAX(l.xpos) as max_x,
                MIN(l.ypos) as min_y,
                MAX(l.ypos) as max_y,
                COUNT(*) as space_count
            FROM ComiketMapWC m
            JOIN ComiketLayoutWC l ON m.comiketNo = l.comiketNo AND m.id = l.mapId
            GROUP BY m.id
            ORDER BY m.id
        """)
        return [
            {
                "id": row["id"],
                "name": row["name"],
                "filename": row["filename"],
                "min_x": row["min_x"],
                "max_x": row["max_x"],
                "min_y": row["min_y"],
                "max_y": row["max_y"],
                "space_count": row["space_count"],
            }
            for row in cursor
        ]

    def get_circle_map_position(self, wcid: int) -> dict | None:
        """Get circle's map position by wcid."""
        if not self._conn:
            return None

        cursor = self._conn.execute(
            """
            SELECT
                c.circleName,
                c.day,
                c.blockId,
                c.spaceNo,
                c.spaceNoSub,
                b.name as blockName,
                l.xpos,
                l.ypos,
                l.mapId,
                m.name as mapName,
                m.filename as mapFilename
            FROM ComiketCircleExtend e
            JOIN ComiketCircleWC c ON e.comiketNo = c.comiketNo AND e.id = c.id
            JOIN ComiketBlockWC b ON c.comiketNo = b.comiketNo AND c.blockId = b.id
            JOIN ComiketLayoutWC l ON c.comiketNo = l.comiketNo
                AND c.blockId = l.blockId AND c.spaceNo = l.spaceNo
            JOIN ComiketMapWC m ON l.comiketNo = m.comiketNo AND l.mapId = m.id
            WHERE e.WCId = ?
            """,
            (wcid,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        space_sub = "a" if row["spaceNoSub"] == 0 else "b"
        return {
            "circle_name": row["circleName"],
            "day": row["day"],
            "block": row["blockName"],
            "space": f"{row['spaceNo']:02d}{space_sub}",
            "xpos": row["xpos"],
            "ypos": row["ypos"],
            "map_id": row["mapId"],
            "map_name": row["mapName"],
            "map_filename": row["mapFilename"],
        }

    def render_hall_map(
        self,
        map_id: int,
        highlight_x: int | None = None,
        highlight_y: int | None = None,
        height: int = 20,
        max_width: int = 100,
    ) -> str:
        """Render ASCII overview of a hall map.

        Args:
            map_id: The map ID to render
            highlight_x: X coordinate to highlight with ★
            highlight_y: Y coordinate to highlight with ★
            height: Output height in lines (width calculated from aspect ratio)
            max_width: Maximum output width in characters

        Returns:
            ASCII art representation of the hall
        """
        if not self._conn:
            return "データベースが開かれていません"

        # Get map bounds
        cursor = self._conn.execute(
            """
            SELECT
                MIN(xpos) as min_x, MAX(xpos) as max_x,
                MIN(ypos) as min_y, MAX(ypos) as max_y
            FROM ComiketLayoutWC
            WHERE mapId = ?
            """,
            (map_id,),
        )
        bounds = cursor.fetchone()
        if not bounds or bounds["max_x"] is None:
            return "マップデータがありません"

        min_x, max_x = bounds["min_x"], bounds["max_x"]
        min_y, max_y = bounds["min_y"], bounds["max_y"]

        # Add padding
        padding = 20
        min_x -= padding
        max_x += padding
        min_y -= padding
        max_y += padding

        # Calculate dimensions preserving aspect ratio (based on height)
        x_range = max_x - min_x
        y_range = max_y - min_y
        aspect_ratio = x_range / y_range

        # Calculate width from height and aspect ratio
        # Terminal characters are typically ~2x taller than wide, so adjust
        width = int(height * aspect_ratio * 2)
        width = min(width, max_width)  # Cap at max_width

        x_scale = x_range / width
        y_scale = y_range / height

        # Create empty grid
        grid = [[" " for _ in range(width)] for _ in range(height)]

        # Get all spaces and plot them
        cursor = self._conn.execute(
            "SELECT xpos, ypos FROM ComiketLayoutWC WHERE mapId = ?",
            (map_id,),
        )
        for row in cursor:
            x = int((row["xpos"] - min_x) / x_scale)
            y = int((row["ypos"] - min_y) / y_scale)
            if 0 <= x < width and 0 <= y < height:
                grid[y][x] = "."

        # Highlight target position
        if highlight_x is not None and highlight_y is not None:
            hx = int((highlight_x - min_x) / x_scale)
            hy = int((highlight_y - min_y) / y_scale)
            if 0 <= hx < width and 0 <= hy < height:
                grid[hy][hx] = "★"

        # Build output with border
        lines = []
        lines.append("┌" + "─" * width + "┐")
        for row in grid:
            lines.append("│" + "".join(row) + "│")
        lines.append("└" + "─" * width + "┘")

        return "\n".join(lines)
