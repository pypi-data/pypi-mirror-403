from asyncio import create_subprocess_exec, subprocess
from pathlib import Path
from random import choice
from re import match
from shutil import move, rmtree
from uuid import uuid4

from ytdlp_simple.config import INVIDIOUS_INSTANCES, YT_ID_PATTERN, logger
from ytdlp_simple.type import MediaContainers
from ytdlp_simple.paths import TMP_DIR


def extract_yt_id(input_str: str) -> str:
    """extracts YouTube video ID from URL or string"""
    found = YT_ID_PATTERN.search(input_str)
    if found:
        return found.group(1)
    if len(input_str) == 11 and match(r'^[a-zA-Z0-9_-]{11}$', input_str):
        return input_str
    return ''


def is_youtube_url(url: str) -> bool:
    """checks if the URL is a YouTube link"""
    return bool(extract_yt_id(url))


def get_invidious_url(video_id: str, instance: str = None) -> str:
    """generates Invidious instance URL"""
    instance = instance or choice(INVIDIOUS_INSTANCES)
    return f'https://{instance}/watch?v={video_id}'


def filter_netscape_cookies(cookies_files: list[Path]) -> list[Path]:
    """
    filters list of files, contains valid Netscape cookies

    Args:
        cookies_files: List of paths to cookies files

    Returns:
        List of paths to Netscape HTTP Cookie format files
    """
    if not cookies_files:
        return []

    valid_cookies = []
    signature = 'Netscape HTTP Cookie File'.lower()

    for file_path in cookies_files:
        try:
            if not file_path.is_file():
                continue
            with file_path.open('r', encoding='utf-8') as f:
                header = f.read(256)

            if signature in header.lower():
                valid_cookies.append(file_path)

        except (OSError, UnicodeDecodeError, PermissionError):
            continue
    return valid_cookies


def get_cookie_arg(cookies_folder: Path | str) -> list[str]:
    """
    returns yt-dlp argument for cookies if txt cookies-files
    in Netscape-format exist in the specified folder
    """
    if cookies_folder is None:
        return []
    cookies_folder = Path(cookies_folder).resolve()
    cookies_files = filter_netscape_cookies(
        list(cookies_folder.glob('*.txt')) if cookies_folder.exists() else []
    )
    if not cookies_files:
        logger.warning(f'no valid cookies found in "{str(cookies_folder)}"')
        return []
    else:
        logger.info(f'found {len(cookies_files)} valid cookies')
        return ['--cookies', choice(cookies_files).resolve().as_posix()]


def create_task_dir() -> Path:
    """creates a unique subfolder for the task avoiding collisions"""
    task_id = str(uuid4())[:8]
    task_dir = TMP_DIR / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    return task_dir


def cleanup_task_dir(task_dir: Path):
    """remove temporary task folder"""
    try:
        if task_dir.exists() and task_dir.is_dir():
            rmtree(task_dir, ignore_errors=True)
    except Exception as e:
        logger.warning(f"failed to cleanup {task_dir}: {e}")


def move_to_output(src: Path, dst_dir: Path, filename: str = None) -> Path:
    """moves file to the output folder with overwriting"""
    dst_dir.mkdir(parents=True, exist_ok=True)
    dst = dst_dir / (filename or src.name)

    if dst.exists():
        dst.unlink()

    move(str(src), str(dst))
    return dst


def find_closest_resolution(target: int, available: list[int], prefer_lower: bool = True) -> int:
    """
    finds closest resolution to target

    Args:
        target: target resolution
        available: list of available resolutions
        prefer_lower: prefer lower resolution when no exact resolution is available
    """
    if not available:
        return target

    # exact match
    if target in available:
        return target

    if prefer_lower:
        # maximum among values less than the target
        lower = [r for r in available if r <= target]
        if lower:
            return max(lower)
        # minimum of the largest ones
        return min(available)
    else:
        # minimum among values not less than the target
        higher = [r for r in available if r >= target]
        if higher:
            return min(higher)
        return max(available)


def get_container_compatibility(container: MediaContainers) -> dict:
    """returns compatible codecs for container"""
    return {
        'mp4': {'video': ['h264', 'avc', 'hevc', 'h265', 'av1', 'vp9'], 'audio': ['aac', 'mp4a', 'opus', 'mp3']},
        'mkv': {'video': ['h264', 'avc', 'hevc', 'h265', 'av1', 'vp9', 'vp8'], 'audio': ['opus', 'aac', 'mp4a', 'vorbis', 'flac', 'mp3']},
        'webm': {'video': ['vp9', 'vp8', 'av1'], 'audio': ['opus', 'vorbis']},
        'mov': {'video': ['h264', 'avc', 'hevc', 'h265', 'prores'], 'audio': ['aac', 'mp4a', 'alac']},
    }.get(container, {'video': [], 'audio': []})


async def run_subprocess(cmd: list[str], check: bool = False) -> tuple[int, str, str]:
    """
    starts subprocess and returns return-code, stdout, stderr
    """
    cmd = [str(c) for c in cmd if c]

    logger.info(f'running: "{" ".join(cmd)}"')

    process = await create_subprocess_exec(
        *cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    stdout_str = stdout.decode('utf-8', errors='replace')
    stderr_str = stderr.decode('utf-8', errors='replace')

    if check and process.returncode != 0:
        logger.error(f'command failed with code {process.returncode}')
        logger.error(f'stderr: {stderr_str[:500]}')

    return process.returncode, stdout_str, stderr_str
