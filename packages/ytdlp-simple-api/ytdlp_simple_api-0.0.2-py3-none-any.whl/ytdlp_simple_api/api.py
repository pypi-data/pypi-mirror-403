"""
FastAPI wrapper for ytdlp_simple download functions.
API writen by Anthropic Claude Opus 4.5

Usage:
    uvicorn ytdlp_simple_api:app --host 0.0.0.0 --port 8000

Environment variables:
    PORT              - Port for listen (default: 7860)
    WEB_UI            - Whether to provide a web interface for downloads and cookie management in browser (default: False)
    HIDE_HOME         - Mask Home Page UI - useful for deployment on HuggingFace Spaces (default: False)
    API_TOKEN         - Bearer token for authentication (default: None)
    DOWNLOADS_DIR     - Directory for downloaded files
    COOKIES_FOLDER    - Folder with cookies.txt files (optional)
    FILE_RETENTION_H  - Hours to keep files before cleanup (default: 0)
"""

from datetime import datetime
from re import sub

from fastapi import BackgroundTasks, FastAPI, UploadFile, File
from fastapi import Depends, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from ytdlp_simple import (
    download_audio_for_transcription,
    download_best_audio,
    download_best_quality,
    download_manual,
    download_video_for_chat,
)

from ytdlp_simple_api.config import (
    DOWNLOADS_DIR,
    COOKIES_FOLDER,
    FILE_RETENTION_H,
    STATIC_DIR,
    HIDE_HOME,
    WEB_UI,
    API_TOKEN
)
from ytdlp_simple_api.depend import verify_token
from ytdlp_simple_api.models import (
    DownloadResponse,
    BestAudioRequest,
    TranscriptionAudioRequest,
    VideoForChatRequest,
    BestQualityRequest,
    ManualDownloadRequest,
    FileInfo, CookieFileInfo, CookieTextRequest
)
from ytdlp_simple_api.utils import (
    _cleanup_old_files,
    _build_response,
    _validate_filename,
    _human_size,
    _path_to_url,
    _extract_domains,
    _is_valid_netscape_cookie,
    _validate_cookie_filename,
    get_fake_home
)

app = FastAPI(
    title='YT-DLP Simple API',
    description='Download videos and audio from YouTube and other platforms',
    version='0.0.1',
    docs_url='/docs',
    redoc_url='/redoc',
    dependencies=[Depends(verify_token)],
)

app.mount('/static', StaticFiles(directory=STATIC_DIR), name='static')


# ─────────────────────────── Endpoints: Downloads ────────────────────


@app.post(
    '/download/best-audio',
    response_model=DownloadResponse,
    summary='Download best quality audio',
    tags=['Download'],
)
async def api_best_audio(
        request: BestAudioRequest,
        background_tasks: BackgroundTasks,
):
    """
    download audio in maximum quality (~130 kbps Opus),
    **use case:** for music, podcasts, high-quality audio extraction.
    """
    background_tasks.add_task(_cleanup_old_files)

    result = await download_best_audio(
        url=request.url,
        output_dir=DOWNLOADS_DIR,
        prefer_lang=request.prefer_lang,
        sponsorblock=request.sponsorblock,
        cookies_folder=COOKIES_FOLDER,
    )
    return _build_response(result)


@app.post(
    '/download/transcription-audio',
    response_model=DownloadResponse,
    summary='Download audio prepared for ASR/transcription',
    tags=['Download'],
)
async def api_transcription_audio(
        request: TranscriptionAudioRequest,
        background_tasks: BackgroundTasks,
):
    """
    download and prepare audio for speech-to-text models.

    **pipeline:** low bitrate → normalize → mono → resample → encode

    **use case:** Whisper, Qwen-3-ASR, Gemma-3n, Microsoft VibeVoice-ASR, etc.
    """
    background_tasks.add_task(_cleanup_old_files)

    result = await download_audio_for_transcription(
        url=request.url,
        output_dir=DOWNLOADS_DIR,
        cookies_folder=COOKIES_FOLDER,
        sample_rate=request.sample_rate,
        output_format=request.output_format,
        prefer_lang=request.prefer_lang,
    )
    return _build_response(result)


@app.post(
    '/download/video-for-chat',
    response_model=DownloadResponse,
    summary='Download video optimized for messengers',
    tags=['Download'],
)
async def api_video_for_chat(
        request: VideoForChatRequest,
        background_tasks: BackgroundTasks,
):
    """
    download video for Telegram/WhatsApp/etc.

    **quality:** 480p/360p, minimal bitrate, smallest he-aac audio, FPS ≤ 30

    correctly handles vertical videos (Shorts, Reels, TikTok).
    """
    background_tasks.add_task(_cleanup_old_files)

    result = await download_video_for_chat(
        url=request.url,
        output_dir=DOWNLOADS_DIR,
        prefer_lang=request.prefer_lang,
        sponsorblock=request.sponsorblock,
        cookies_folder=COOKIES_FOLDER,
    )
    return _build_response(result)


@app.post(
    '/download/best-quality',
    response_model=DownloadResponse,
    summary='Download video in maximum quality',
    tags=['Download'],
)
async def api_best_quality(
        request: BestQualityRequest,
        background_tasks: BackgroundTasks,
):
    """
    download video in maximum available quality.

    typically: best VP9/AV1 video + best Opus audio.

    **use case:** archiving, editing, high-quality viewing.
    """
    background_tasks.add_task(_cleanup_old_files)

    result = await download_best_quality(
        url=request.url,
        output_dir=DOWNLOADS_DIR,
        prefer_lang=request.prefer_lang,
        sponsorblock=request.sponsorblock,
        cookies_folder=COOKIES_FOLDER,
        container=request.container,
    )
    return _build_response(result)


@app.post(
    '/download/manual',
    response_model=DownloadResponse,
    summary='Download with manual quality settings',
    tags=['Download'],
)
async def api_manual(
        request: ManualDownloadRequest,
        background_tasks: BackgroundTasks,
):
    """
    full control over download parameters.

    specify resolution, codecs, bitrate, container, etc.
    """
    background_tasks.add_task(_cleanup_old_files)

    result = await download_manual(
        url=request.url,
        output_dir=DOWNLOADS_DIR,
        max_resolution=request.max_resolution,
        audio_bitrate=request.audio_bitrate,
        vcodec=request.vcodec,
        acodec=request.acodec,
        speech_lang=request.speech_lang,
        limit_fps=request.limit_fps,
        container=request.container,
        sponsorblock=request.sponsorblock,
        cookies_folder=COOKIES_FOLDER,
    )
    return _build_response(result)


# ─────────────────────────── Endpoints: Files ────────────────────────


@app.get(
    '/files/{filename}',
    summary='Download a file',
    tags=['Files'],
    response_class=FileResponse,
)
async def get_file(filename: str):
    """
    download a previously created file by its name.

    files are automatically deleted after the retention period.
    """
    _validate_filename(filename)
    file_path = DOWNLOADS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail='File not found or expired')

    # determine media type
    suffix = file_path.suffix.lower()
    media_types = {
        '.mp4': 'video/mp4',
        '.mkv': 'video/x-matroska',
        '.webm': 'video/webm',
        '.mov': 'video/quicktime',
        '.mp3': 'audio/mpeg',
        '.opus': 'audio/opus',
        '.ogg': 'audio/ogg',
        '.flac': 'audio/flac',
        '.wav': 'audio/wav',
        '.m4a': 'audio/mp4',
    }
    media_type = media_types.get(suffix, 'application/octet-stream')

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type,
    )


@app.get(
    '/files',
    response_model=list[FileInfo],
    summary='List all available files',
    tags=['Files'],
)
async def list_files():
    """list all downloaded files with their metadata."""
    files = []
    for file_path in DOWNLOADS_DIR.iterdir():
        if file_path.is_file():
            stat = file_path.stat()
            files.append(FileInfo(
                filename=file_path.name,
                size_bytes=stat.st_size,
                size_human=_human_size(stat.st_size),
                created_at=datetime.fromtimestamp(stat.st_mtime),
                download_url=_path_to_url(file_path),
            ))
    return sorted(files, key=lambda f: f.created_at, reverse=True)


@app.delete(
    '/files/{filename}',
    summary='Delete a file',
    tags=['Files'],
)
async def delete_file(filename: str):
    """manually delete a downloaded file."""
    _validate_filename(filename)
    file_path = DOWNLOADS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail='File not found')

    try:
        file_path.unlink()
        return {'status': 'deleted', 'filename': filename}
    except OSError as e:
        raise HTTPException(status_code=500, detail=f'Failed to delete: {e}')


@app.get('/ui', response_class=HTMLResponse, tags=['UI'], include_in_schema=False, dependencies=[])
@app.get('/ui/', response_class=HTMLResponse, tags=['UI'], include_in_schema=False, dependencies=[])
async def ui_page():
    """serve web UI"""
    if not WEB_UI:
        raise HTTPException(status_code=403, detail="WEB UI disabled: environment variable 'WEB_UI' not set")
    html_path = STATIC_DIR / 'ui.html'
    if not html_path.exists():
        raise HTTPException(status_code=404, detail='UI not found')
    content = html_path.read_text(encoding='utf-8')
    if not API_TOKEN:
        content = content.replace('class="auth"', 'class="hide"')
    if FILE_RETENTION_H > 0:
        content = content.replace('files-list__content__warning hide', 'files-list__content__warning')
    return HTMLResponse(content)


# ─────────────────────────── Endpoints: System ───────────────────────


@app.get('/', summary='Health check', tags=['System'], dependencies=[])
async def health():
    """service health check and configuration info."""
    if not HIDE_HOME:
        return HTMLResponse(get_fake_home())
    status = {
        'status': 'ok',
        'service': 'ytdlp-simple-api',
        'config': {
            'downloads_dir': str(DOWNLOADS_DIR),
            'cookies_configured': COOKIES_FOLDER is not None,
            'file_retention_hours': FILE_RETENTION_H,
        },
    }
    return JSONResponse(status)


@app.post('/cleanup', summary='Trigger file cleanup', tags=['System'])
async def trigger_cleanup():
    """manually trigger cleanup of expired files."""
    deleted = await _cleanup_old_files()
    return {
        'status': 'completed',
        'deleted_files': deleted,
        'retention_hours': FILE_RETENTION_H,
    }


# ─────────────────────────── Cookies ──────────────────────────────

@app.get(
    '/cookies',
    response_model=list[CookieFileInfo],
    summary='List cookie files',
    tags=['Cookies'],
    dependencies=[Depends(verify_token)],
)
async def list_cookies():
    """list all uploaded cookie files."""
    files = []

    for file_path in COOKIES_FOLDER.iterdir():
        if file_path.is_file() and file_path.suffix == '.txt':
            stat = file_path.stat()

            # read and validate
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                is_valid = _is_valid_netscape_cookie(content)
                domain_hint = _extract_domains(content) if is_valid else None
            except Exception:  # noqa
                is_valid = False
                domain_hint = None

            files.append(CookieFileInfo(
                filename=file_path.name,
                size_bytes=stat.st_size,
                size_human=_human_size(stat.st_size),
                modified_at=datetime.fromtimestamp(stat.st_mtime),
                is_valid=is_valid,
                domains=domain_hint,
            ))

    return sorted(files, key=lambda f: f.filename)


@app.post(
    '/cookies',
    summary='Upload cookie file',
    tags=['Cookies'],
    dependencies=[Depends(verify_token)],
)
async def upload_cookie(
        file: UploadFile = File(..., description='Netscape format cookie .txt file'),
):
    """
    upload a cookie file in Netscape format.

    to export cookies from browser, use extensions like:
    - "Get cookies.txt LOCALLY" (Chrome/Firefox)
    - "cookies.txt" (Firefox)
    """
    # Validate filename
    filename = file.filename or 'cookies.txt'

    # sanitize filename
    filename = sub(r'[^\w\-_.]', '_', filename)
    if not filename.endswith('.txt'):
        filename += '.txt'

    # read content
    try:
        content = await file.read()
        content_str = content.decode('utf-8', errors='ignore')
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'Failed to read file: {e}')

    # validate format
    if not _is_valid_netscape_cookie(content_str):
        raise HTTPException(
            status_code=400,
            detail='Invalid cookie format. Expected Netscape cookie file format.'
        )

    # check size (max 1MB)
    if len(content) > 1024 * 1024:
        raise HTTPException(status_code=400, detail='File too large (max 1MB)')

    # save
    file_path = COOKIES_FOLDER / filename
    try:
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to save: {e}')

    return {
        'status': 'uploaded',
        'filename': filename,
        'size': _human_size(len(content)),
        'domain_hint': _extract_domains(content_str),
    }


@app.delete(
    '/cookies/{filename}',
    summary='Delete cookie file',
    tags=['Cookies'],
    dependencies=[Depends(verify_token)],
)
async def delete_cookie(filename: str):
    """
    delete a cookie file.
    """
    _validate_cookie_filename(filename)

    file_path = COOKIES_FOLDER / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail='cookie file not found')

    try:
        file_path.unlink()
        return {'status': 'deleted', 'filename': filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to delete: {e}')


@app.get(
    '/cookies/{filename}',
    summary='View cookie file info',
    tags=['Cookies'],
    dependencies=[Depends(verify_token)],
    response_model=CookieFileInfo,
)
async def get_cookie_info(filename: str):
    """
    get info about a specific cookie file.
    """
    _validate_cookie_filename(filename)

    file_path = COOKIES_FOLDER / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="cookie file not found")

    stat = file_path.stat()

    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        is_valid = _is_valid_netscape_cookie(content)
        domain_hint = _extract_domains(content) if is_valid else None
    except Exception:  # noqa
        is_valid = False
        domain_hint = None

    return CookieFileInfo(
        filename=file_path.name,
        size_bytes=stat.st_size,
        size_human=_human_size(stat.st_size),
        modified_at=datetime.fromtimestamp(stat.st_mtime),
        is_valid=is_valid,
        domains=domain_hint,
    )


@app.post(
    '/cookies/text',
    summary='Create cookie file from text',
    tags=['Cookies'],
    dependencies=[Depends(verify_token)],
)
async def create_cookie_from_text(body: CookieTextRequest):
    """create a cookie file by pasting content."""
    filename = body.filename.strip()
    filename = sub(r'[^\w\-_.]', '_', filename)
    if not filename.endswith('.txt'):
        filename += '.txt'

    content = body.content

    if not _is_valid_netscape_cookie(content):
        raise HTTPException(
            status_code=400,
            detail='invalid cookie format. Expected Netscape cookie file format.'
        )

    content_bytes = content.encode('utf-8')
    if len(content_bytes) > 1024 * 1024:
        raise HTTPException(status_code=400, detail='content too large (max 1MB)')

    file_path = COOKIES_FOLDER / filename
    try:
        file_path.write_bytes(content_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'failed to save: {e}')

    return {
        'status': 'created',
        'filename': filename,
        'size': _human_size(len(content_bytes)),
        'domains': _extract_domains(content),
    }


# ─────────────────────────── Cookies UI ──────────────────────────────

@app.get('/cookies-ui', response_class=HTMLResponse, tags=['UI'], include_in_schema=False, dependencies=[])
@app.get('/cookies-ui/', response_class=HTMLResponse, tags=['UI'], include_in_schema=False, dependencies=[])
async def cookies_ui_page():
    """serve the cookies management UI."""
    if not WEB_UI:
        raise HTTPException(status_code=403, detail="WEB UI disabled: environment variable 'WEB_UI' not set")
    html_path = STATIC_DIR / 'cookies.html'
    if not html_path.exists():
        raise HTTPException(status_code=404, detail='cookies UI not found')
    content = html_path.read_text(encoding='utf-8')
    if not API_TOKEN:
        content = content.replace('class="auth"', 'class="hide"')
    return HTMLResponse(content)


__all__ = [
    'app',
]
