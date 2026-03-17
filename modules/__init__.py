"""AI Video Editor — Modular Pipeline Modules."""

from dataclasses import dataclass, field


@dataclass
class VideoInfo:
    path: str
    width: int
    height: int
    fps: float
    duration: float
    has_audio: bool
    codec: str


@dataclass
class Scene:
    start: float
    end: float
    type: str  # "cut", "fade", "dissolve"


@dataclass
class WordTimestamp:
    start: float
    end: float
    word: str


@dataclass
class CaptionSegment:
    start: float
    end: float
    text: str
    words: list[WordTimestamp] = field(default_factory=list)


@dataclass
class Transcription:
    language: str
    duration: float
    segments: list[CaptionSegment] = field(default_factory=list)


@dataclass
class EnergySegment:
    start: float
    end: float
    level: float
    is_highlight: bool


@dataclass
class FaceRegion:
    x: int
    y: int
    w: int
    h: int
    timestamp: float


@dataclass
class EditList:
    cuts: list[tuple[float, float]] = field(default_factory=list)  # (start, end) segments to KEEP
    speed_map: list[tuple[float, float, float]] = field(default_factory=list)  # (start, end, speed)
