import sqlite3
import feedparser
from typing import List, Tuple, Optional


class DB:
    """Manages podcast feed metadata in a SQLite database.

    Provides CRUD operations for podcast RSS feeds, including automatic
    metadata extraction via feedparser. Ensures data integrity with
    unique RSS URLs and supports safe concurrent usage.

    The database schema includes:
        - id (INTEGER PRIMARY KEY)
        - title (TEXT, NOT NULL)
        - author (TEXT)
        - rss_url (TEXT, UNIQUE, NOT NULL)
        - category (TEXT)
        - episode_count (INTEGER, DEFAULT 0)
        - description (TEXT)
        - cover_url (TEXT)
        - added_at (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

    Usage:
        >>> with GetFeed("podcasts.db") as db:
        ...     db.add_feed("https://example.com/feed.xml")
        ...     feeds = db.fetch_feeds()
        ...     print(f"Loaded {len(feeds)} feeds")

    Attributes:
        con (sqlite3.Connection): Database connection object.
        cur (sqlite3.Cursor): Database cursor for execution.

    Note:
        - RSS URLs are normalized (stripped of whitespace) and enforced as UNIQUE.
        - Adding an existing feed updates its metadata (title, author, etc.).
        - Designed for single-threaded use; for multi-threading, use separate instances.
    """

    def __init__(self, db_path: str = "data.db") -> None:

        self.con = sqlite3.connect(db_path)
        self.cur = self.con.cursor()
        self._create_table()

    def _create_table(self) -> None:
        """Create feed table with full podcast metadata."""
        self.cur.execute(
            """
        CREATE TABLE IF NOT EXISTS feed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT,
            rss_url TEXT UNIQUE NOT NULL,
            category TEXT,
            episode_count INTEGER DEFAULT 0,
            description TEXT,
            cover_url TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        )
        self.con.commit()

    def add_feed(self, url: str):
        """
        Parse RSS feed and insert podcast metadata.
        Returns:
            int: id of inserted row on success
            str: error message on failure
        """
        try:
            # Parse feed
            feed = feedparser.parse(url)

            # Handle parse errors
            if hasattr(feed, "bozo") and feed.bozo:
                error_msg = f"Feed parse error: {feed.bozo_exception}"
                print(f"Warning: {error_msg}")

            # Validate that feed has basic podcast structure
            if not hasattr(feed, 'entries') or len(feed.entries) == 0:
                error_msg = "Feed has no episodes"
                print(f"Error: {error_msg} - {url}")
                return error_msg
            
            # Check if entries have required podcast fields (title and enclosures for audio)
            first_entry = feed.entries[0]
            if not hasattr(first_entry, 'title') or not first_entry.title:
                error_msg = "Feed entries missing title"
                print(f"Error: {error_msg} - {url}")
                return error_msg
            
            # Check for audio enclosures (typical for podcasts)
            if not hasattr(first_entry, 'enclosures') or len(first_entry.enclosures) == 0:
                print(f"Warning: Feed entries may not have audio content - {url}")

            # Extract metadata (with fallbacks)
            title = getattr(feed.feed, "title", "").strip() or "Untitled Podcast"
            author = (
                getattr(feed.feed, "author", "")
                or getattr(feed.feed, "itunes_author", "")
                or ""
            ).strip()

            description = (
                getattr(feed.feed, "description", "")
                or getattr(feed.feed, "summary", "")
                or ""
            ).strip()

            # Extract cover image
            cover_url = None
            if hasattr(feed.feed, "image") and hasattr(feed.feed.image, "href"):
                cover_url = feed.feed.image.href
            elif hasattr(feed.feed, "itunes_image") and hasattr(
                feed.feed.itunes_image, "href"
            ):
                cover_url = feed.feed.itunes_image.href

            # Count episodes
            episode_count = len(feed.entries)

            # Clean URL (remove extra spaces)
            clean_url = url.strip()

            # 🔒 Parameterized insert (prevents SQL injection)
            self.cur.execute(
                """
                INSERT INTO feed
                (title, author, rss_url, category, episode_count, description, cover_url)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(rss_url) DO UPDATE SET
                    title = excluded.title,
                    author = excluded.author,
                    episode_count = excluded.episode_count,
                    description = excluded.description,
                    cover_url = excluded.cover_url,
                    added_at = CURRENT_TIMESTAMP
            """,
                (
                    title,
                    author,
                    clean_url,
                    "",  # category (optional - could extract from tags)
                    episode_count,
                    description,
                    cover_url,
                ),
            )
            self.con.commit()
            return self.cur.lastrowid

        except Exception as e:
            error_msg = f"Failed to add feed: {e}"
            print(f"{error_msg} - {url}")
            return error_msg

    def fetch_feeds(self) -> List[Tuple]:
        """Fetch all feeds as list of tuples."""
        self.cur.execute(
            "SELECT id, title, author, rss_url, category, episode_count FROM feed"
        )
        return self.cur.fetchall()

    def fetch_feed_by_id(self, feed_id: int) -> Optional[dict]:
        """Fetch single feed as dict."""
        self.cur.execute(
            """
            SELECT id, title, author, rss_url, category, episode_count, 
                   description, cover_url, added_at 
            FROM feed 
            WHERE id = ?
        """,
            (feed_id,),
        )

        row = self.cur.fetchone()
        if row:
            return {
                "id": row[0],
                "title": row[1],
                "author": row[2],
                "rss_url": row[3],
                "category": row[4],
                "episode_count": row[5],
                "description": row[6],
                "cover_url": row[7],
                "added_at": row[8],
            }
        return None

    def delete_feed(self, feed_id: int) -> bool:
        """Delete feed by ID."""
        try:
            self.cur.execute("DELETE FROM feed WHERE id = ?", (feed_id,))
            self.con.commit()
            return self.cur.rowcount > 0
        except Exception as e:
            print(f"❌ Delete failed: {e}")
            return False

    def close(self) -> None:
        """Close database connection."""
        if self.con:
            self.con.close()

    # Context manager support (optional but recommended)
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
