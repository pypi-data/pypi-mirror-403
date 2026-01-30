from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from remotivelabs.broker.recording_session.repeat import PlaybackRepeat


@dataclass
class RecordingSessionPlaybackStatus:
    """
    Represents the playback status of a recording session.
    """

    path: str
    mode: PlaybackMode
    offset: int
    repeat: PlaybackRepeat | None = None


class RecordingSessionPlaybackError(Exception):
    """Exception raised for errors during recording session playback."""


class PlaybackMode(Enum):
    """Playback modes for a recording session."""

    PLAYBACK_PLAYING = 0
    """Playing a file."""
    PLAYBACK_PAUSED = 1
    """Playback is paused."""
    PLAYBACK_CLOSED = 2
    """Playback is closed."""
