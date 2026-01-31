#models.py

from dataclasses import dataclass
from typing import Optional


@dataclass
class EmotionMetrics:
    pitch: float
    rms: float
    delta_pitch: float
    delta_rms: float


@dataclass
class TranscriptSegment:
    start: float
    end: float
    speaker: str
    text: str
    emotion: Optional[EmotionMetrics] = None
