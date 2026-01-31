from datetime import datetime, timedelta
from pathlib import Path
from random import choice

from fastapi import HTTPException

from ytdlp_simple_api.config import DOWNLOADS_DIR, FILE_RETENTION_H
from ytdlp_simple_api.models import DownloadResponse


def _path_to_url(file_path: Path) -> str:
    """convert local path to downloadable URL."""
    return f"/files/{file_path.name}"


def _human_size(size_bytes: int) -> str:
    """convert bytes to human-readable format."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def _validate_filename(filename: str) -> None:
    """prevent path traversal attacks."""
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")


async def _cleanup_old_files() -> int:
    """remove files older than retention period. Returns count of deleted files."""
    if not DOWNLOADS_DIR.exists() or FILE_RETENTION_H <= 0:
        return 0

    cutoff = datetime.now() - timedelta(hours=FILE_RETENTION_H)
    deleted = 0

    for file_path in DOWNLOADS_DIR.iterdir():
        if file_path.is_file():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff:
                try:
                    file_path.unlink()
                    deleted += 1
                except OSError:
                    pass
    return deleted


def _build_response(result) -> DownloadResponse:
    """convert DownloadResult to API response."""
    if result.success and result.path:
        return DownloadResponse(
            success=True,
            file_url=_path_to_url(result.path),
            filename=result.path.name,
            warnings=result.warnings or [],
        )
    return DownloadResponse(
        success=False,
        error=result.error,
        warnings=result.warnings or [],
    )


def _validate_cookie_filename(filename: str) -> None:
    """validate cookie filename for security."""
    if not filename:
        raise HTTPException(status_code=400, detail="Filename required")
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only .txt files allowed")


def _is_valid_netscape_cookie(content: str) -> bool:
    """check if content looks like a valid Netscape cookie file."""
    lines = content.strip().split('\n')

    # Check for Netscape header or valid cookie lines
    has_header = any('netscape' in line.lower() or 'cookie' in line.lower()
                     for line in lines[:3])

    # domain, flag, path, secure, expiry, name, value (tab-separated)
    valid_lines = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split('\t')
        if len(parts) >= 6:
            valid_lines += 1

    return has_header or valid_lines > 0


def _extract_domains(content: str) -> list[str]:
    """extract known media platform domains from cookie file."""
    found_domains = set()

    # platforms
    target_platforms = {
        'youtube.com': 'YouTube',
        'google.com': 'Google',
        'twitter.com': 'Twitter',
        'x.com': 'X (Twitter)',
        'instagram.com': 'Instagram',
        'tiktok.com': 'TikTok',
        'twitch.tv': 'Twitch',
        'facebook.com': 'Facebook',
        'vk.com': 'VK',
        'rutube.ru': 'Rutube',
        'soundcloud.com': 'SoundCloud',
        'vimeo.com': 'Vimeo',
        'bilibili.com': 'Bilibili',
        'spotify.com': 'Spotify',
        'discord.com': 'Discord',
        'patreon.com': 'Patreon',
    }

    # нelper to check if a domain string matches a target
    def check_domain(d_str: str):
        d_str = d_str.lower().lstrip('.')
        for target, name in target_platforms.items():
            if d_str == target or d_str.endswith('.' + target):
                return name
        return None

    # scan only first columns of lines that look like cookies
    for line in content.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split('\t')
        if len(parts) >= 1:
            raw_domain = parts[0]
            if raw_domain:
                platform = check_domain(raw_domain)
                if platform:
                    found_domains.add(platform)

    return sorted(list(found_domains))


def get_fake_home() -> str:
    fake_home = choice((
        'https://huggingface.co/spaces?sdk=docker&hardware=gpu',
        'https://huggingface.co/models?pipeline_tag=text-to-image&num_parameters=min%3A0%2Cmax%3A12B&sort=trending',
        'https://xenova-florence2-webgpu.static.hf.space/index.html',
        'https://xenova-whisper-speaker-diarization.static.hf.space/index.html',
        'https://huggingfacefw-blogpost-fineweb-v1.static.hf.space/index.html',
        'https://huggingfacefw-blogpost-fineweb-v1.static.hf.space/index.html',
        'https://cloudgpu-runpod-free-credits.static.hf.space/index.html',
        'https://gpucloud-runpod-free-trial.static.hf.space/index.html'
    ))
    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
    body,html{{height:100%;margin:0;padding:0;overflow:hidden}}iframe{{width:100%;height:100%;border:none;display:block}}
    </style>
    </head><body><iframe src="{fake_home}"></iframe></body></html>
    '''
