from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np


class CallbackEventType(Enum):
    """Types of callback events that can be sent to the callback thread."""

    VAD_CHANGED = "vad_changed"
    SPEECH_START = "speech_start"
    SPEECH_CHUNK = "speech_chunk"
    AUDIO_CHUNK = "audio_chunk"
    SPEECH_ENDED = "speech_ended"


@dataclass
class CallbackEvent:
    """Represents a callback event to be processed."""

    event_type: CallbackEventType
    data: dict


@dataclass
class VADConfig:
    """Configuration for Voice Activity Detection."""

    threshold: float = 0.5
    padding_before_ms: int = 300
    padding_after_ms: int = 300
    max_silence_ms: int = 1000
    min_speech_duration_ms: int = 250
    max_speech_duration_s: float = 60.0

    def __post_init__(self) -> None:
        """Validate VAD configuration."""
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("VAD threshold must be between 0.0 and 1.0")
        if self.padding_before_ms < 0:
            raise ValueError("Padding before must be non-negative")
        if self.padding_after_ms < 0:
            raise ValueError("Padding after must be non-negative")
        if self.max_silence_ms <= 0:
            raise ValueError("Max silence duration must be positive")


@dataclass
class SpeechChunk:
    """Represents a chunk of speech audio with timing information.

    Attributes:
        audio_chunk: The audio data as a numpy array
        start_time: Start time of the chunk in seconds
        end_time: End time of the chunk in seconds
        duration: Duration of the chunk in seconds
    """

    audio_chunk: np.ndarray
    start_time: float
    end_time: float
    duration: float
