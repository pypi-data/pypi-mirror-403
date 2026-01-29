import json
import pygame
import time
import feedparser
from rich.text import Text
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.containers import Container, Horizontal, VerticalScroll, Vertical
from textual.widgets import Header, Footer, Static, Label, Input, Button, ProgressBar
from textual.screen import Screen
from textual.events import Click
from .db import DB
from .core import htmlpraser
from .player import Player


# Feed item component for predefined feeds
class FeedItem(Static):
    def __init__(self, feed_id, feed_data):
        super().__init__()
        self.feed_id = feed_id
        self.feed_data = feed_data

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical():
                yield Static(f"🎙️ [bold]{self.feed_data['name']}[/bold]", classes="feed-name")
                yield Static(self.feed_data['description'], classes="feed-description")
            yield Button("Add", variant="primary", id=f"add-{self.feed_id}", classes="add-feed-btn")

# Podcast box component
class PodcastBox(Static):
    def __init__(self, name, url):
        super().__init__()
        self.podcast_name = name
        self.url = url

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static(
                f"🎙️ [bold]{self.podcast_name}[/bold]\n[dim]{self.url}[/dim]", classes="info"
            )
            yield Button("Play", variant="success", classes="play-btn")


# Add Feed Form Screen
class AddFeedScreen(Screen):
    """Popup screen for adding new podcast feeds."""

    # Mapping of button IDs to RSS URLs and descriptions
    PREDEFINED_FEEDS = {
        "feed-1": {
            "url": "https://feeds.megaphone.fm/darknetdiaries",
            "name": "Darknet Diaries",
            "description": "True stories from the dark side of the Internet.",
        },
        "feed-2": {
            "url": "https://feeds.twit.tv/sn.xml",
            "name": "Security Now",
            "description": "Weekly security news with Steve Gibson and Leo Laporte.",
        },
        "feed-3": {
            "url": "https://feeds.simplecast.com/3Y_p_T3I",  # Hacker Valley Studio (Working link)
            "name": "Hacker Valley Studio",
            "description": "Exploring the human condition in cybersecurity.",
        },
        "feed-4": {
            "url": "https://feeds.npr.org/510318/podcast.xml",  # NPR Up First
            "name": "NPR Up First",
            "description": "The biggest stories and ideas of the day from NPR.",
        },
        "feed-5": {
            "url": "https://podcasts.files.bbci.co.uk/p02nq0gn.rss",
            "name": "BBC Global News",
            "description": "The latest news from the BBC World Service.",
        },
        "feed-6": {
            "url": "https://feeds.simplecast.com/54nAGcIl",
            "name": "The Daily (NYT)",
            "description": "This is how the news should sound. From The New York Times.",
        },
        "feed-7": {
            "url": "https://feeds.simplecast.com/4qg_LgQw",
            "name": "Syntax.fm",
            "description": "Full Stack Web Development Podcast.",
        },
        "feed-8": {
            "url": "https://changelog.com/podcast/feed",
            "name": "The Changelog",
            "description": "Conversations with open source maintainers and leaders.",
        },
        "feed-9": {
            "url": "https://changelog.com/jsparty/feed",
            "name": "JS Party",
            "description": "A community celebration of JavaScript and the web.",
        },
        "feed-10": {
            "url": "http://feeds.wnyc.org/radiolab",
            "name": "Radiolab",
            "description": "A show about curiosity. Where sound illuminates ideas.",
        },
        "feed-11": {
            "url": "https://feeds.99percentinvisible.org/99percentinvisible",
            "name": "99% Invisible",
            "description": "A tiny radio show about design and architecture.",
        },
        "feed-12": {
            "url": "https://feeds.megaphone.fm/sciencevs",
            "name": "Science Vs",
            "description": "Taking on fads, and the internet, with science.",
        },
    }

    CSS = """
    #top-bar {
        height: 3;
        padding: 1;
        background: $boost;
    }
    #back-btn {
        width: auto;
        margin-right: 1;
    }
    #add-feed-form {
        height: 100%;
        background: $surface;
    }
    #predefined-feeds {
        height: auto;
        max-height: 60%;
        padding: 2;
        margin-bottom: 1;
        border-bottom: solid $accent;
    }
    #predefined-title {
        text-style: bold;
        margin-bottom: 2;
        text-align: center;
    }
    .category-title {
        text-style: bold;
        color: $primary;
        margin-top: 2;
        margin-bottom: 1;
        background: $primary;
        color: white;
        padding: 0 1;
    }
    FeedItem {
        background: $surface;
        border: solid $accent;
        margin: 1 0;
        padding: 1;
         
        height: 8;
    }
    FeedItem > Horizontal {
        min-height: 3;
        align: left top;
    }
    .feed-name {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    .feed-description {
        color: $text-muted;
        margin-bottom: 0;
    }
    .add-feed-btn {
        width: auto;
        min-width: 10;
        margin-left: 2;
    }
    #form-container {
        height: auto;
        padding: 2;
    }
    #form-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #url-input {
        width: 100%;
        margin-bottom: 1;
    }
    #form-buttons {
        height: auto;
        margin-top: 2;
    }
    #add-button {
        width: 50%;
        margin-right: 1;
    }
    #cancel-button {
        width: 50%;
    }
    """

    def compose(self) -> ComposeResult:
        with Horizontal(id="top-bar"):
            yield Button("← Back", variant="success", id="back-btn")

        with Container(id="add-feed-form"):
            with VerticalScroll(id="feed-list-container"):
                yield Label("🛡️ Technology & Hacking", classes="category-title")
                yield FeedItem("feed-1", self.PREDEFINED_FEEDS["feed-1"])
                yield FeedItem("feed-2", self.PREDEFINED_FEEDS["feed-2"])
                yield FeedItem("feed-3", self.PREDEFINED_FEEDS["feed-3"])

                yield Label("📰 News & Current Affairs", classes="category-title")
                yield FeedItem("feed-4", self.PREDEFINED_FEEDS["feed-4"])
                yield FeedItem("feed-5", self.PREDEFINED_FEEDS["feed-5"])
                yield FeedItem("feed-6", self.PREDEFINED_FEEDS["feed-6"])

                yield Label("💻 Technology & Development", classes="category-title")
                yield FeedItem("feed-7", self.PREDEFINED_FEEDS["feed-7"])
                yield FeedItem("feed-8", self.PREDEFINED_FEEDS["feed-8"])
                yield FeedItem("feed-9", self.PREDEFINED_FEEDS["feed-9"])

                yield Label("🎨 Science & Design", classes="category-title")
                yield FeedItem("feed-10", self.PREDEFINED_FEEDS["feed-10"])
                yield FeedItem("feed-11", self.PREDEFINED_FEEDS["feed-11"])
                yield FeedItem("feed-12", self.PREDEFINED_FEEDS["feed-12"])
        
            with VerticalScroll(id="form-container"):
                yield Label("Or Add Custom Feed", id="form-title")
                yield Label("RSS Feed URL:", classes="label")
                yield Input(placeholder="https://example.com/feed.xml", id="url-input")
                yield Label("Feed Title (Optional):", classes="label")
                yield Input(placeholder="Custom title (auto-detected if empty)", id="title-input")
                yield Label("Author (Optional):", classes="label")
                yield Input(placeholder="Author name", id="author-input")
                with Horizontal(id="form-buttons"):
                    yield Button("Add Feed", variant="primary", id="add-button")
                    yield Button("Cancel", variant="default", id="cancel-button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks in the form."""
        if event.button.id == "back-btn":
            self.app.pop_screen()
        elif event.button.id == "add-button":
            self.add_feed()
        elif event.button.id == "cancel-button":
            self.dismiss()
        elif event.button.id.startswith("add-") and event.button.id[4:] in self.PREDEFINED_FEEDS:
            feed_id = event.button.id[4:]
            url = self.PREDEFINED_FEEDS[feed_id]["url"]
            self.add_feed(url)

    def add_feed(self, url=None) -> None:
        """Add feed to database and update UI."""
        if url is None:
            url_input = self.query_one("#url-input", Input)
            url = url_input.value.strip()

        if not url:
            self.notify("Please enter a valid RSS feed URL", severity="error")
            return

        try:
            db = DB()
            result = db.add_feed(url)
            db.close()

            if isinstance(result, int):
                self.notify(f"Feed added successfully!", severity="success")
                # Refresh the main screen's feed list before dismissing
                self.app.query_one("#main-space").remove_children()
                self.dismiss()
                # Trigger a reload of feeds on the main screen
                self.app.load_feeds()
            else:
                self.notify(f"Failed to add feed: {result}", severity="error")

        except Exception as e:
            self.notify(f"Error adding feed: {e}", severity="error")


class CastAwayApp(App):
    CSS = """
    #top-bar {
        height: 5;
        padding: 1;
        background: $boost;
    }
    #search-input {
        width: 70%;
    }
    #add-btn {
        width: 30%;
        margin-left: 1;
    }
    #main-space {
        padding: 1;
    }
    PodcastBox {
        background: $surface;
        margin: 1 0;
        padding: 1;
        border: solid $accent;
        height: auto;
    }
    PodcastBox > Horizontal {
        height: auto;
        align: center middle;
    }
    .info {
        width: 1fr;
        height: auto;
    }
    .play-btn {
        width: auto;
        min-width: 8;
        margin-left: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.all_feeds = []

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="top-bar"):
            yield Input(placeholder="Search...", id="search-input")
            yield Button("Add New Feed", variant="primary", id="add-btn")
        with VerticalScroll(id="main-space"):
            pass

        yield Footer()

    def on_mount(self) -> None:
        """Load feeds when the app starts."""
        self.load_feeds()

    def load_feeds(self) -> None:
        """Load and display feeds from database."""
        db = DB()
        feeds = db.fetch_feeds()
        self.all_feeds = feeds
        self.display_feeds(feeds)
        db.close()

    def display_feeds(self, feeds) -> None:
        """Display given feeds in the main space."""
        main_space = self.query_one("#main-space")
        main_space.remove_children()

        if not feeds:
            podcast_box = PodcastBox("No feeds found", "null")
            main_space.mount(podcast_box)
        else:
            for feed in feeds:
                podcast_box = PodcastBox(feed[1], feed[3])  # title, rss_url
                main_space.mount(podcast_box)

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes and filter feeds."""
        if event.input.id == "search-input":
            search_term = event.value.lower().strip()
            if search_term:
                # Filter feeds by title or author
                filtered_feeds = [
                    feed for feed in self.all_feeds
                    if search_term in feed[1].lower() or search_term in (feed[2] or "").lower()
                ]
                self.display_feeds(filtered_feeds)
            else:
                # Show all feeds if search is empty
                self.display_feeds(self.all_feeds)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button clicks."""
        if event.button.id == "add-btn":
            # Push the add feed screen
            self.push_screen(AddFeedScreen())

        # Handle play buttons on podcast boxes
        elif "play-btn" in event.button.classes:
            podcast_box = event.button.parent.parent
            if podcast_box and hasattr(podcast_box, "url"):
                self.push_screen(Feed(podcast_box.url))
                print(f"Navigating to Feed screen with URL: {podcast_box.url}")

    def on_screen_resume(self) -> None:
        """Reload feeds when returning from add feed screen."""
        self.load_feeds()

class Feed(Screen):

    CSS = """
     
    #back-btn {
        background: blue;
        color: white;

        width: auto;
        height: 1;
        min-height: 1;

        padding: 0 1;
        margin-bottom: 1 ;

    }
    #back-btn:hover {
        background: darkblue;
    }
    #feed-container {
        height: 100%;
        layout: vertical;
    }
    #podcast-details {
        padding: 0 2 2 2 ;
        background: $boost;
        margin-bottom: 1;
        border: solid $primary;
        height: auto;
    }
    .podcast-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    .podcast-author {
        color: $text-muted;
        margin-top: 1;
       
    }
    .podcast-description {
        color: $text;
    }
    #episodes-list {
        padding: 1;
        height: 1fr;
    }
    .episode-row {
        padding: 1 2;
        margin: 0 0 1 0;
        border: solid $accent;
        background: $surface;
        align: center top;
        height: 5;
    }
    .row {
         
        height: 3;
    }
    .episode-row:hover {
        background: $panel;
    }
    .play-episode-btn {
        width: auto;
        min-width: 8;
        margin-right: 2;
        background: $success;
        color: $text;
    }
    .episode-title {
        text-style: bold;
        margin-bottom: 1;
    }
    .episode-description {
        color: $text-muted;
        margin-bottom: 1;
    }
    .episode-duration {
        color: $primary;
        text-style: italic;
    }
    .section-title {
        text-style: bold;
        margin-bottom: 1;
    }
    """

    def __init__(self, url: str) -> None:
        super().__init__()
        self.url = url
        self.episodes = []
        
        try:
            # Parse feed with timeout
            feed = feedparser.parse(url)
            
            # Check for parsing errors
            if feed.bozo and feed.bozo_exception:
                print(f"Feed parsing warning: {feed.bozo_exception}")
            
            # Get feed metadata with fallbacks
            self.podcast_title = getattr(feed.feed, 'title', 'Unknown Podcast')
            self.author = (
                getattr(feed.feed, 'author', '') or 
                getattr(feed.feed, 'itunes_author', '') or 
                getattr(feed.feed, 'author_detail', {}).get('name', '') or
                'Unknown Author'
            )
            self.description = htmlpraser(
                getattr(feed.feed, 'description', '') or 
                getattr(feed.feed, 'summary', '') or 
                'No description'
            )
            
            # Map actual episodes from feedparser with full data
            if hasattr(feed, 'entries') and feed.entries:
                for i, entry in enumerate(feed.entries):
                    try:
                        episode = {
                            "title": htmlpraser(getattr(entry, "title", f"Episode {i+1}")),
                            "description": htmlpraser(
                                getattr(entry, "description", "") or getattr(entry, "summary", "")
                            ),
                            "duration": getattr(entry, "itunes_duration", "Unknown"),
                            "published": getattr(entry, "published", ""),
                            "link": getattr(entry, "link", ""),
                            "summary": htmlpraser(getattr(entry, "summary", "")),
                            "author": getattr(entry, "author", "") or getattr(entry, "author_detail", {}).get('name', ''),
                            "enclosures": getattr(entry, "enclosures", []),
                            "media_content": getattr(entry, "media_content", []),
                            "content": getattr(entry, "content", []),
                            "rss_url": url,  # Add feed URL for context
                        }
                        self.episodes.append(episode)
                    except Exception as e:
                        print(f"Error parsing episode {i}: {e}")
                        continue
            else:
                print("No entries found in feed")
        except Exception as e:
            print(f"Error parsing feed: {e}")
            import traceback
            traceback.print_exc()
            self.podcast_title = "Error Loading Feed"
            self.author = "Unknown"
            self.description = f"Failed to load feed: {str(e)}"

    def compose(self) -> ComposeResult:

        with Container(id="feed-container"):
            # Top podcast details
            yield Static("◀ Back", id="back-btn")
            with Container(id="podcast-details"):

                yield Label(f"🎙️ [bold]{self.podcast_title}[/bold]", classes="podcast-title")

                yield Static(f"{self.description}",expand=True, classes="podcast-description")

                yield Label(f"Author : {self.author}", classes="podcast-author")
                yield Label(f"Episodes : {len(self.episodes)}", classes="podcast-author")

            # Episodes list
            with VerticalScroll(id="episodes-list"):
                yield Static("Episodes", classes="section-title")
                for i, episode in enumerate(self.episodes):
                    with Horizontal(classes="episode-row"):
                        yield Button("▶️", variant="success", classes="play-episode-btn", id=f"play-{i}")
                        with Container(id=f"episode-{i}"):
                            yield Label(f"[bold]{episode['title']}[/bold]", classes="episode-title")
                            yield Label(episode['description'], classes="episode-description")
                            yield Label(f"Duration: {episode['duration']}", classes="episode-duration")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()
        elif event.button.id and event.button.id.startswith("play-"):
            index = int(event.button.id.split("-")[1])
            episode = self.episodes[index]

            self.app.push_screen(Playing(episode))

    def on_click(self, event: Click) -> None:
        widget = event.widget
        while widget:
            if widget.id and widget.id.startswith("episode-"):
                index = int(widget.id.split("-")[1])
                episode = self.episodes[index]
                self.app.push_screen(Episode(episode))
                return

            if widget.id == "back-btn":
                self.app.pop_screen()
                return
            widget = widget.parent

class Episode(Screen):

    CSS = """
    #back-btn {
        background: blue;
        color: white;

        width: auto;
        height: 1;
        min-height: 1;

        padding: 0 1;
        margin-bottom: 1 ;

    }
    #back-btn:hover {
        background: darkblue;
    }
    #episode-container {
        height: 100%;
        layout: vertical;
    }
    #episode-details {
        padding: 2;
        background: $boost;
        margin-bottom: 1;
        border: solid $primary;
        height: auto;
    }
    .episode-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }
    .episode-description {
        color: $text-muted;
        margin-bottom: 1;
    }
    .episode-duration {
        color: $primary;
        
        margin-bottom: 1;
    }
    
    #play-btn {
        padding: 0 2;
        margin-bottom: 1;
        background: $success;
        color: $text;
    
    }
    """

    def __init__(self, episode) -> None:
        super().__init__()
        self.episode = episode
        self.playing = False

    def compose(self) -> ComposeResult:
        epi_title = Text(f"🎙️ Episode {self.episode['title']}", justify="center")
        epi_title.stylize("bold white")

        with Container(id="episode-container"):
            # Episode details
            yield Static("◀ Back", id="back-btn")
            with Container(id="episode-details"):
                yield Label(
                    epi_title,
                    classes="episode-title",
                )
                yield Static(
                    f"{self.episode['description'][:512]}...", classes="episode-description"
                )
                yield Label(
                    f"Author: {self.episode['author']}",
                    classes="episode-duration",
                )
                yield Label(
                    f"Published: {self.episode['published']}",
                    classes="episode-duration",
                )
                yield Label(
                    f"Duration: {self.episode['duration']}", classes="episode-duration"
                )

                yield Button("▶️ Play Episode", variant="success", id="play-btn")
            # Player controls

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()
        elif event.button.id == "play-btn":
            self.app.push_screen(Playing(self.episode))

    def on_click(self, event: Click) -> None:
        widget = event.widget
        while widget:

            if widget.id == "back-btn":
                self.app.pop_screen()
                return
            widget = widget.parent

class Playing(ModalScreen):
    """Audio player screen."""

    CSS = """
    #container {
        height: 100%;
        width: 100%;
        background: $panel;
    }
    
    #header {
        dock: top;
        width: 100%;
        height: 3;
        background: $primary;
        color: white;
        text-align: center;
        content-align: center middle;
    }
    
    #header:hover {
        background: $primary-darken-1;
    }
    
    #main {
        width: 100%;
        height: 100%;
        align: center middle;
        padding: 2;
    }
    
    .card {
        width: 90;
        height: auto;
        background: $boost;
        border: thick $primary;
        padding: 3;
    }
    
    .title {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $accent;
        margin-bottom: 2;
    }
    
    .info {
        width: 100%;
        text-align: center;
        color: $text;
        margin-bottom: 1;
    }
    
    .status {
        width: 100%;
        text-align: center;
        text-style: bold;
        color: $success;
        margin: 2 0;
    }
    
    .progress-container {
        width: 100%;
        height: auto;
        align: center middle;
        margin: 1 0;
    }
    
    .time-left {
        width: auto;
        color: $accent;
        text-style: bold;
        padding: 0 1;
    }
    
    .progress {
        width: 1fr;
        height: 1;
        text-align: center;
        color: $primary;
        text-style: bold;
    }
    
    .time-right {
        width: auto;
        color: $text-muted;
        padding: 0 1;
    }
    
    .spacer {
        height: 1;
    }
    
    .controls {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 2;
    }
    
    .btn {
        margin: 0 1;
    }
    
    #play-btn {
        min-width: 20;
        background: $success;
    }
    
    #download-progress-container {
        display: none;
    }
    
    #download-progress-container.downloading {
        display: block;
    }
    
    #playback-progress-container {
        display: block;
    }
    
    #playback-progress-container.downloading {
        display: none;
    }
    """

    def __init__(self, episode):
        super().__init__()
        self.episode = episode
        self.player = None
        self.timer = None
        self.episode_duration = self._parse_duration()
    
    def _parse_duration(self):
        """Parse duration from episode metadata."""
        # Try different duration fields
        dur = (self.episode.get("itunes_duration") or 
               self.episode.get("duration") or
               self.episode.get("itunes_length"))
        
        if not dur:
            return None
        
        # Convert to string and clean
        dur = str(dur).strip()
        
        # If it's already a number (seconds), return it
        try:
            return float(dur)
        except ValueError:
            pass
        
        # Parse HH:MM:SS or MM:SS format
        if ":" in dur:
            parts = dur.split(":")
            try:
                if len(parts) == 3:  # HH:MM:SS
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                elif len(parts) == 2:  # MM:SS
                    return int(parts[0]) * 60 + int(parts[1])
            except ValueError:
                pass
        
        return None
    
    def compose(self) -> ComposeResult:
        with Container(id="container"):
            yield Button("← Back", id="header")
            
            with Container(id="main"):
                with Vertical(classes="card"):
                    yield Label("♪ NOW PLAYING", classes="title")
                    
                    yield Static(
                        self.episode.get("title", "Unknown"),
                        classes="info"
                    )
                    
                    author = (self.episode.get("author") or
                             self.episode.get("itunes_author") or
                             "Unknown")
                    yield Static(f"by {author}", classes="info")
                    
                    yield Label("⏳ Loading...", id="status", classes="status")
                    
                    # Download progress bar (hidden by default, shown during download)
                    with Horizontal(id="download-progress-container", classes="progress-container"):
                        yield Static("📥", id="download-icon", classes="time-left")
                        yield Static("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", id="download-progress", classes="progress")
                        yield Static("0%", id="download-percent", classes="time-right")
                    
                    # Playback progress bar with time labels on sides
                    with Horizontal(id="playback-progress-container", classes="progress-container"):
                        yield Static("00:00:00", id="current", classes="time-left")
                        yield Static("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", id="progress", classes="progress")
                        yield Static("00:00:00", id="total", classes="time-right")
                    
                    # Empty line for spacing
                    yield Static("", classes="spacer")
                    
                    # Main controls: Seek back, Play/Pause, Seek forward
                    with Horizontal(classes="controls"):
                        yield Button("⏪ -10s", id="back", classes="btn")
                        yield Button("▶ Play", id="play-btn", classes="btn")
                        yield Button("+30s ⏩", id="forward", classes="btn")
        
        yield Footer()
    
    def on_mount(self):
        """Start playback."""
         
        
        # Debug: Print episode duration info
        print(f"\n=== Episode Info ===")
        print(f"Title: {self.episode.get('title', 'Unknown')}")
        print(f"itunes_duration: {self.episode.get('itunes_duration')}")
        print(f"duration: {self.episode.get('duration')}")
        print(f"Parsed duration: {self.episode_duration} seconds")
        if self.episode_duration:
            print(f"Formatted: {self._fmt(self.episode_duration)}")
        print(f"===================\n")
        
        self.player = Player()
        
        success = self.player.load_and_play(self.episode)
        
        if not success:
            self.query_one("#status").update("✗ Error: No audio URL")
            self.notify("Failed to load episode", severity="error")
        else:
            self.notify("Loading...", severity="information")
        
        # Update UI every 100ms for smooth real-time progress
        self.timer = self.set_interval(0.1, self.update_ui)
    
    def update_ui(self):
        """Update UI with current playback state in real-time."""
        if not self.player:
            return
        
        try:
            status = self.player.get_status()
            
            # Get real-time current position
            current = self.player.get_current_time()
            
            # Use episode metadata duration first, then player duration
            duration = self.episode_duration
            if not duration or duration <= 0:
                duration = self.player.get_duration()
            
            # Debug output less frequently
            if not hasattr(self, '_update_count'):
                self._update_count = 0
            self._update_count += 1
            
            # Only log every 50 updates (every 5 seconds at 0.1s interval)
            if self._update_count % 50 == 0:
                print(f"[Real-time] Current: {current:.2f}s / Duration: {duration:.2f}s = {(current/duration*100) if duration > 0 else 0:.1f}%")
            
            # Update status label
            status_widget = self.query_one("#status")
            if status == "loading":
                # Show download progress with MB downloaded
                downloaded_mb = 0
                total_mb = 0
                progress_percent = 0
                
                if self.player:
                    downloaded_bytes = self.player.get_download_progress() * self.player.get_total_content_length()
                    downloaded_mb = downloaded_bytes / (1024 * 1024)
                    total_bytes = self.player.get_total_content_length()
                    total_mb = total_bytes / (1024 * 1024) if total_bytes > 0 else 0
                    progress_percent = self.player.get_download_progress() * 100
                
                if total_mb > 0:
                    status_widget.update(f"⏳ Downloading: {downloaded_mb:.1f}MB / {total_mb:.1f}MB ({progress_percent:.0f}%)")
                else:
                    status_widget.update(f"⏳ Downloading: {downloaded_mb:.1f}MB")
                status_widget.styles.color = "yellow"
            elif status == "playing":
                # Hide download progress bar and show playback progress
                self.query_one("#download-progress-container").set_class(False, "downloading")
                self.query_one("#playback-progress-container").set_class(False, "downloading")
                
                status_widget.update("▶ Playing")
                status_widget.styles.color = "green"
            elif status == "paused":
                # Hide download progress bar and show playback progress
                self.query_one("#download-progress-container").set_class(False, "downloading")
                self.query_one("#playback-progress-container").set_class(False, "downloading")
                
                status_widget.update("⏸ Paused")
                status_widget.styles.color = "orange"
            elif status == "error":
                # Hide download progress bar and show playback progress
                self.query_one("#download-progress-container").set_class(False, "downloading")
                self.query_one("#playback-progress-container").set_class(False, "downloading")
                
                error = self.player.get_error()
                status_widget.update(f"✗ {error}")
                status_widget.styles.color = "red"
            else:
                # Hide download progress bar and show playback progress
                self.query_one("#download-progress-container").set_class(False, "downloading")
                self.query_one("#playback-progress-container").set_class(False, "downloading")
                
                status_widget.update("⏹ Ready")
                status_widget.styles.color = "blue"
            
            # Update download progress bar during loading
            if status == "loading" and self.player:
                # Show download progress bar and hide playback progress
                self.query_one("#download-progress-container").set_class(True, "downloading")
                self.query_one("#playback-progress-container").set_class(True, "downloading")
                
                # Update download progress bar
                progress_percent = self.player.get_download_progress() * 100
                bar = self._make_progress_bar(progress_percent, width=40)
                self.query_one("#download-progress").update(bar)
                self.query_one("#download-percent").update(f"{progress_percent:.0f}%")
            
            # Update time displays in real-time
            current_widget = self.query_one("#current")
            total_widget = self.query_one("#total")
            
            current_widget.update(self._fmt(current))
            total_widget.update(self._fmt(duration))
            
            # Calculate real-time progress percentage
            # Formula: (current_time / total_duration) * 100
            if duration and duration > 0:
                # Real-time percentage calculation
                progress_percent = (current / duration) * 100
                
                # Clamp between 0 and 100
                progress_percent = min(100.0, max(0.0, progress_percent))
                
                # Create progress bar with calculated percentage
                bar = self._make_progress_bar(progress_percent, width=40)
                
                # Update the progress bar widget
                progress_widget = self.query_one("#progress")
                progress_widget.update(bar)
            else:
                # No duration yet, show empty bar
                progress_widget = self.query_one("#progress")
                bar = self._make_progress_bar(0, width=40)
                progress_widget.update(bar)
            
            # Update play button state
            play_btn = self.query_one("#play-btn")
            if self.player.is_paused:
                play_btn.label = "▶ Resume"
            elif self.player.is_playing:
                play_btn.label = "⏸ Pause"
            else:
                play_btn.label = "▶ Play"
        
        except Exception as e:
            print(f"UI update error: {e}")
            import traceback
            traceback.print_exc()
    
    def _fmt(self, seconds):
        """Format seconds as HH:MM:SS."""
        if not seconds or seconds < 0:
            return "00:00:00"
        
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _make_progress_bar(self, progress: float, width: int = 50) -> str:
        """Create custom ASCII progress bar.
        
        Args:
            progress: Progress percentage (0-100)
            width: Width of the bar in characters
            
        Returns:
            ASCII art progress bar string
        """
        if progress < 0:
            progress = 0
        if progress > 100:
            progress = 100
        
        filled_width = int((progress / 100) * width)
        empty_width = width - filled_width
        
        # Style options (choose one):
        
        # Style 1: Heavy bar with triangle playhead
        if filled_width > 0:
            bar = "━" * (filled_width - 1) + "▶" + "─" * empty_width
        else:
            bar = "▶" + "─" * (width - 1)
        
        # Style 2: Blocks (uncomment to use)
        # if filled_width > 0:
        #     bar = "█" * (filled_width - 1) + "▶" + "░" * empty_width
        # else:
        #     bar = "▶" + "░" * (width - 1)
        
        # Style 3: Double line (uncomment to use)
        # if filled_width > 0:
        #     bar = "═" * (filled_width - 1) + "▶" + "─" * empty_width
        # else:
        #     bar = "▶" + "─" * (width - 1)
        
        # Style 4: Dots (uncomment to use)
        # if filled_width > 0:
        #     bar = "●" * (filled_width - 1) + "▶" + "○" * empty_width
        # else:
        #     bar = "▶" + "○" * (width - 1)
        
        return bar
    
    def on_button_pressed(self, event):
        """Handle button clicks."""
        if not self.player:
            return
        
        btn_id = event.button.id
        
        if btn_id == "header":
            self.cleanup()
            self.app.pop_screen()
        
        elif btn_id == "play-btn":
            # Play/Pause toggle
            if self.player.is_playing and not self.player.is_paused:
                self.player.pause()
                self.notify("⏸ Paused", severity="information")
            elif self.player.is_paused:
                self.player.resume()
                self.notify("▶ Resumed", severity="information")
            else:
                # If stopped but same episode is loaded, just start playing
                if (self.player.current_episode and
                    self.player.audio_data_buffer and
                    self.player._get_audio_url(self.episode) == self.player.audio_url):
                    pygame.mixer.music.play()
                    self.player.is_playing = True
                    self.player.status = "playing"
                    self.player.start_time = time.time()
                    self.notify("▶ Playing", severity="information")
                else:
                    # Different episode or no audio loaded - load and play
                    self.player.load_and_play(self.episode)
                    self.notify("▶ Playing", severity="information")
        
        elif btn_id == "back":
            # Seek back 10 seconds
            current = self.player.get_current_time()
            new_position = max(0, current - 10)
            self.player.seek(new_position)
            self.notify("⏪ -10s", severity="information")
        
        elif btn_id == "forward":
            # Seek forward 30 seconds
            current = self.player.get_current_time()
            duration = self.episode_duration or self.player.get_duration()
            new_position = min(duration, current + 30) if duration > 0 else current + 30
            self.player.seek(new_position)
            self.notify("⏩ +30s", severity="information")
    
    def cleanup(self):
        """Stop playback and cleanup."""
        if self.timer:
            self.timer.stop()
        
        if self.player:
            self.player.stop()
    
    def on_unmount(self):
        """Called when screen closes."""
        self.cleanup()
