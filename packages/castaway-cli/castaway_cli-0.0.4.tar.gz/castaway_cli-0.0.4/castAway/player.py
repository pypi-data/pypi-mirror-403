"""
Podcast Player - Direct Episode Playback
"""

import pygame
import threading
import time
import requests
import io
from typing import Optional, Dict, Any


class Player:
    """Audio player that plays episodes directly."""

    def __init__(self):
        """Initialize pygame mixer."""
        # Using default settings, which are sufficient for pygame.mixer.music
        pygame.mixer.init() 

        self.current_episode: Optional[Dict[str, Any]] = None
        self.audio_url: str = ""
        self.audio_data_buffer: Optional[io.BytesIO] = None

        # Status
        self.is_playing = False
        self.is_paused = False
        self.status = "idle"  # idle, loading, playing, paused, error
        self.error_message = ""

        # Download tracking
        self.download_progress = 0.0  # 0.0 to 1.0
        self.total_content_length = 0

        # Playback timing - CRITICAL for real-time updates
        self.duration = 0.0
        self.start_time = 0.0  # When playback started
        self.pause_position = 0.0  # Position when paused

        # Threading
        self.load_thread: Optional[threading.Thread] = None
        self.stop_flag = False

        print("✓ Player initialized (using mixer.music)")

    def load_and_play(self, episode: Dict[str, Any]) -> bool:
        """Load episode and start playing.

        Args:
            episode: Episode dict with title, enclosures, etc.

        Returns:
            True if started successfully
        """
        # Check if this is the same episode that's already loaded
        episode_url = self._get_audio_url(episode)
        if (self.current_episode and episode_url == self.audio_url and
            self.audio_data_buffer is not None):
            
            # Same episode - just resume or start playing
            if self.is_paused:
                self.resume()
                return True
            elif not self.is_playing:
                # If we have audio data but not playing, start playing
                if self.audio_data_buffer:
                    pygame.mixer.music.play()
                    self.is_playing = True
                    self.status = "playing"
                    self.start_time = time.time()
                    return True
            
            # Already playing the same episode
            return True
        
        # Different episode or no audio loaded - stop and load new episode
        self.stop()

        self.current_episode = episode
        self.status = "loading"
        self.error_message = ""
        self.stop_flag = False

        # Extract audio URL
        self.audio_url = episode_url
        if not self.audio_url:
            self.status = "error"
            self.error_message = "No audio URL found in episode"
            return False

        # Start loading in background
        self.load_thread = threading.Thread(target=self._load_audio_worker, daemon=True)
        self.load_thread.start()

        return True

    def _get_audio_url(self, episode: Dict[str, Any]) -> Optional[str]:
        """Extract audio URL from episode."""
        print(f"\nExtracting audio URL...")

        # Try enclosures first
        if "enclosures" in episode and episode["enclosures"]:
            print(f"Found {len(episode['enclosures'])} enclosure(s)")
            for enc in episode["enclosures"]:
                if hasattr(enc, "href"):
                    print(f"  Using enclosure href: {enc.href}")
                    return enc.href
                elif hasattr(enc, "url"):
                    print(f"  Using enclosure url: {enc.url}")
                    return enc.url
                elif isinstance(enc, dict):
                    url = enc.get("href") or enc.get("url")
                    if url:
                        print(f"  Using enclosure dict: {url}")
                        return url

        # Try links (feedparser format)
        if "links" in episode and episode["links"]:
            print(f"Found {len(episode['links'])} link(s)")
            for link in episode["links"]:
                # Look for enclosure links
                if isinstance(link, dict):
                    if link.get("rel") == "enclosure":
                        url = link.get("href")
                        if url:
                            print(f"  Using enclosure link: {url}")
                            return url
                elif hasattr(link, "rel") and link.rel == "enclosure":
                    if hasattr(link, "href"):
                        print(f"  Using link href: {link.href}")
                        return link.href

        # Try media_content
        if "media_content" in episode and episode["media_content"]:
            print(f"Found media_content")
            for media in episode["media_content"]:
                if hasattr(media, "url"):
                    print(f"  Using media url: {media.url}")
                    return media.url
                elif isinstance(media, dict):
                    url = media.get("url")
                    if url:
                        print(f"  Using media dict: {url}")
                        return url

        # Try links for audio URLs (alternative links)
        if "links" in episode and episode["links"]:
            for link in episode["links"]:
                url = None
                if isinstance(link, dict):
                    url = link.get("href")
                elif hasattr(link, "href"):
                    url = link.href

                if url and self._is_audio_url(url):
                    print(f"  Using audio link: {url}")
                    return url

        print("  ✗ No audio URL found")
        return None

    def _is_audio_url(self, url: str) -> bool:
        """Check if URL looks like audio."""
        if not url:
            return False
        url = url.lower()
        return any(ext in url for ext in [".mp3", ".m4a", ".wav", ".ogg", ".aac"])

    def _load_audio_worker(self):
        """Background worker to download and load audio."""
        try:
            print(f"Loading: {self.audio_url}")

            # Download audio
            self.download_progress = 0.0
            self.total_content_length = 0

            # Stream download audio
            with requests.get(self.audio_url, stream=True, timeout=30) as response:
                response.raise_for_status()

                # Get total size for progress calculation
                content_length = response.headers.get('content-length')
                if content_length:
                    self.total_content_length = int(content_length)
                    print(f"Total size: {self.total_content_length / (1024*1024):.2f} MB")

                downloaded_size = 0
                audio_data_parts = []
                
                for chunk in response.iter_content(chunk_size=8192):
                    if self.stop_flag:
                        return
                    
                    audio_data_parts.append(chunk)
                    downloaded_size += len(chunk)
                    
                    if self.total_content_length > 0:
                        self.download_progress = downloaded_size / self.total_content_length

                audio_data = b"".join(audio_data_parts)
                
                # Ensure progress is 1.0 if we successfully finished downloading
                self.download_progress = 1.0
            
            if self.stop_flag:
                return

            print(f"Downloaded {len(audio_data) / (1024*1024):.2f} MB")

            # Load into pygame
            audio_buffer = io.BytesIO(audio_data)
            self.audio_data_buffer = audio_buffer # Store the buffer
            
            # Load audio into mixer.music
            pygame.mixer.music.load(self.audio_data_buffer)

            # We lose self.sound.get_length() but rely on self.duration being set elsewhere (e.g., in UI)

            if self.stop_flag:
                return

            # Start playing
            pygame.mixer.music.play()
            self.is_playing = True
            self.status = "playing"
            self.start_time = time.time()  # CRITICAL: Record exact start time

            print(f"✓ Playing (duration: {self.duration:.1f}s - from feed/UI)")
            print(f"  Start time recorded: {self.start_time:.3f}")
            print(f"  Real-time progress will update 10x per second in UI")

            # Monitor playback with real-time logging
            last_log = time.time()
            # Use pygame.mixer.music.get_busy() to monitor playback
            while pygame.mixer.music.get_busy():
                if self.stop_flag:
                    return

                # Log every 3 seconds
                current_time = time.time()
                if current_time - last_log >= 3:
                    # Calculate elapsed time based on tracking. This is a robust way to get time,
                    # even with seeking, until get_current_time is refactored to use get_pos().
                    elapsed = current_time - self.start_time 
                    progress_percent = (
                        (elapsed / self.duration * 100) if self.duration > 0 else 0
                    )
                    print(
                        f"  [Player] {elapsed:.1f}s / {self.duration:.1f}s ({progress_percent:.1f}%)"
                    )
                    last_log = current_time

                time.sleep(0.1)

            # Finished
            if not self.stop_flag:
                self.is_playing = False
                self.status = "idle"
                print("Playback finished")

        except Exception as e:
            print(f"Error: {e}")
            self.status = "error"
            self.error_message = str(e)
            self.is_playing = False

    def pause(self):
        """Pause playback."""
        if self.is_playing and not self.is_paused:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.status = "paused"
            self.pause_position = time.time() - self.start_time

    def resume(self):
        """Resume playback."""
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.status = "playing"
            self.start_time = time.time() - self.pause_position

    def stop(self):
        """Stop playback."""
        self.stop_flag = True

        # Stop mixer.music playback
        pygame.mixer.music.stop()

        # Clean up in-memory buffer to free resources
        if self.audio_data_buffer:
            self.audio_data_buffer.close()
            self.audio_data_buffer = None

        self.is_playing = False
        self.is_paused = False
        self.status = "idle"

        if self.load_thread and self.load_thread.is_alive():
            self.load_thread.join(timeout=1.0)

    def seek(self, seconds: float):
        """Seek to a specific position.

        Args:
            seconds: Position to seek to in seconds
        """
        # Note: If duration is 0, seeking is likely impossible or unreliable anyway
        if self.status in ["idle", "loading", "error"]:
            print("⚠ Cannot seek: Audio not loaded or status is invalid.")
            return

        # Clamp to valid range
        if seconds < 0:
            seconds = 0
        if self.duration > 0 and seconds > self.duration:
            seconds = self.duration

        print(f"⏩ Seeking to {seconds:.1f}s")

        was_paused = self.is_paused
        
        # Pygame mixer.music.set_pos is the reliable way to seek for long audio
        # It takes time in seconds (float).
        pygame.mixer.music.set_pos(seconds)

        # Update timing to reflect new position
        # This ensures the UI reflects the new position instantly via get_current_time
        self.start_time = time.time() - seconds

        # If it was paused, ensure we restore the paused state, as set_pos can sometimes
        # implicitly resume playback depending on the backend.
        if was_paused:
            pygame.mixer.music.pause()
            self.pause_position = seconds
            self.status = "paused"
            print(f"  (Paused at {seconds:.1f}s)")
        else:
            self.is_paused = False
            self.status = "playing"

    def get_current_time(self) -> float:
        """Get current playback position in seconds.

        This is called frequently (10 times per second) so it must be fast
        and accurate for real-time progress bar updates.

        Returns:
            Current position in seconds
        """
        # If paused, return the frozen position
        if self.is_paused:
            return self.pause_position

        # If not playing, return 0
        if not pygame.mixer.music.get_busy():
            return 0.0
        
        # We rely on the time-based calculation (time.time() - self.start_time) 
        # because it already incorporates the seek offset correctly set in self.start_time.
        # This is more robust than trying to combine Pygame's relative get_pos() 
        # with the absolute seek position.

        # Calculate elapsed time since playback started/last seek
        elapsed = time.time() - self.start_time

        # Don't exceed duration
        if self.duration > 0 and elapsed > self.duration:
            elapsed = self.duration

        return elapsed

    def get_duration(self) -> float:
        """Get total duration."""
        return self.duration

    def get_status(self) -> str:
        """Get current status."""
        return self.status

    def get_error(self) -> str:
        """Get error message."""
        return self.error_message

    def get_download_progress(self) -> float:
        """Get current download progress (0.0 to 1.0)."""
        return self.download_progress

    def get_total_content_length(self) -> int:
        """Get total content length in bytes."""
        return self.total_content_length
