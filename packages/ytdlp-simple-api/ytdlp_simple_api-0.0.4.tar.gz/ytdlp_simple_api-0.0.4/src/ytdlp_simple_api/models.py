from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

from ytdlp_simple.type import (
    AudioBitrates,
    AudioCodecs,
    MediaContainers,
    SpeechLangs,
    VideoCodecs,
    VideoResolutions,
)


class DownloadResponse(BaseModel):
    """Unified response for all download endpoints."""
    success: bool
    file_url: Optional[str] = None
    filename: Optional[str] = None
    error: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)

    model_config = {"json_schema_extra": {"examples": [{"success": True, "file_url": "http://localhost:8000/files/video_abc123.mp4", "filename": "video_abc123.mp4", "error": None, "warnings": []}]}}


class BestAudioRequest(BaseModel):
    url: str = Field(..., description="Video URL to download")
    prefer_lang: Optional[list[str]] = Field(default=None, description="Preferred audio languages, e.g. ['ru', 'en']")
    sponsorblock: bool = Field(default=True, description="Remove sponsor/ad segments via SponsorBlock")


class TranscriptionAudioRequest(BaseModel):
    url: str = Field(..., description="Video URL to download")
    sample_rate: Literal[16000, 24000] = Field(default=16000, description="Sample rate in Hz (16kHz for most ASR models)")
    output_format: Literal["opus", "flac", "pcm"] = Field(default="opus", description="Output format: opus (small), flac (lossless), pcm (wav)")
    prefer_lang: Optional[list[str]] = Field(default=None, description="Preferred audio languages")


class VideoForChatRequest(BaseModel):
    url: str = Field(..., description="Video URL to download")
    prefer_lang: Optional[list[str]] = Field(default=None)
    sponsorblock: bool = Field(default=True)


class BestQualityRequest(BaseModel):
    url: str = Field(..., description="Video URL to download")
    prefer_lang: Optional[list[str]] = Field(default=None)
    sponsorblock: bool = Field(default=True)
    container: MediaContainers = Field(default="mp4", description="Container format: mp4, mkv, webm, mov")


class ManualDownloadRequest(BaseModel):
    url: str = Field(..., description="Video URL to download")
    max_resolution: VideoResolutions = Field(default="4k")
    audio_bitrate: AudioBitrates = Field(default="best")
    vcodec: VideoCodecs = Field(default="avc", description="av1/vp9/avc/hevc")
    acodec: AudioCodecs = Field(default="opus", description="opus/aac")
    speech_lang: SpeechLangs = Field(default="ru", description="orig/ru/en")
    limit_fps: bool = Field(default=False, description="Limit to 30 FPS")
    container: MediaContainers = Field(default="mp4")
    sponsorblock: bool = Field(default=True)


class FileInfo(BaseModel):
    filename: str
    size_bytes: int
    size_human: str
    created_at: datetime
    download_url: str


class CookieFileInfo(BaseModel):
    filename: str
    size_bytes: int
    size_human: str
    modified_at: datetime
    is_valid: bool
    domains: list[str] = Field(default_factory=list)


class CookieTextRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=100)
    content: str = Field(..., min_length=10)
