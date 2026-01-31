from dataclasses import dataclass, field, asdict
from json import dumps
from pathlib import Path
from typing import Literal


@dataclass
class DownloadResult:
    """upload result"""
    success: bool
    path: Path | None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return dumps(asdict(self), ensure_ascii=False, default=str, indent=2)


@dataclass
class MediaInfo:
    """information about the media file (parsed from ffmpeg -i)"""
    duration: float = 0.0
    total_bitrate: int = 0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    vcodec: str = ''
    vbitrate: int = 0
    acodec: str = ''
    abitrate: int = 0
    sample_rate: int = 0
    channels: str = ''
    filesize: int = 0


@dataclass
class FormatInfo:
    """information of the format from yt dlp"""
    format_id: str
    ext: str
    height: int = 0
    width: int = 0
    fps: float = 0
    vcodec: str = ''
    acodec: str = ''
    vbr: float = 0
    abr: float = 0
    filesize: int = 0
    language: str = ''
    quality_note: str = ''  # low, medium, etc.


VideoResolutions = Literal['8k', '4k', '2k', '1080p', '720p', '480p', '360p', '240p', '144p']
AudioBitrates = Literal['best', 'medium', 'low']
VideoCodecs = Literal['av1', 'vp9', 'avc', 'hevc']
AudioCodecs = Literal['opus', 'aac']
AudioQuality = Literal['best', 'medium', 'low']
SpeechLangs = Literal['orig', 'ru', 'en']
MediaContainers = Literal['mp4', 'mkv', 'webm', 'mov']
FrameOrientations = Literal['horizontal', 'vertical', 'mixed', 'unknown']
