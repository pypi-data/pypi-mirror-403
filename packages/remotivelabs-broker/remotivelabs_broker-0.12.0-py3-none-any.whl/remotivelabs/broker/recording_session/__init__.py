"""
There is a `RecordingSessionClient` for managing recording session playback on the broker.

```python
.. include:: ../_docs/snippets/recording_session.py
```
"""

from remotivelabs.broker.recording_session.client import RecordingSession, RecordingSessionClient
from remotivelabs.broker.recording_session.file import File
from remotivelabs.broker.recording_session.repeat import PlaybackRepeat
from remotivelabs.broker.recording_session.status import PlaybackMode, RecordingSessionPlaybackError, RecordingSessionPlaybackStatus

__all__ = [
    "File",
    "PlaybackRepeat",
    "PlaybackMode",
    "RecordingSession",
    "RecordingSessionClient",
    "RecordingSessionPlaybackError",
    "RecordingSessionPlaybackStatus",
]
