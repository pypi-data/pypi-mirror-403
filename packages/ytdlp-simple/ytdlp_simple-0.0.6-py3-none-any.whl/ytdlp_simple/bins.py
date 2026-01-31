from asyncio import gather, run, get_running_loop
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from re import match as re_match
from threading import Thread, Event
from typing import TypeVar
from zipfile import ZipFile

from ytdlp_simple.config import logger, BINARIES_SOURCES, BINARIES_UPDATE_DAYS_INTERVAL
from ytdlp_simple.config import os_name
from ytdlp_simple.downloader import download_file, create_progress_bar
from ytdlp_simple.downloader import fetch_json
from ytdlp_simple.paths import is_writable_directory, LIB_DIR, user_data_dir, get_tmp

BINARIES = BINARIES_SOURCES.get(os_name, {})
T = TypeVar('T')

def get_writable_bin_dir() -> Path:
    if is_writable_directory(LIB_DIR):
        writable_bin_dir = LIB_DIR
    else:
        user_dir = user_data_dir() / LIB_DIR.name
        if is_writable_directory(user_dir):
            writable_bin_dir = user_dir
        else:
            writable_bin_dir = get_tmp(LIB_DIR.name)

    bin_dir = writable_bin_dir / 'bin'
    bin_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir


BIN_PATH = get_writable_bin_dir()


@lru_cache(maxsize=5)
def get_bin(name: str, as_str: bool = True) -> str | Path:
    path = (BIN_PATH / (name if os_name != 'windows' else f'{name}.exe')).resolve()
    return path.as_posix() if as_str else path


def is_binary_executable(bin_path: Path):
    bin_path = Path(bin_path)
    if not bin_path.is_file():
        return False

    try:
        with bin_path.open("rb") as f:
            header = f.read(512)
    except OSError:
        return False

    if header.startswith(b"\x7FELF"):
        return True
    elif header.startswith(b"MZ"):
        if len(header) >= 0x40:
            pe_offset = int.from_bytes(header[0x3C:0x40], "little")
            if pe_offset + 4 <= len(header):
                if header[pe_offset:pe_offset + 4] == b"PE\x00\x00":
                    return True
    return False


def unpack(zip_path: Path, final_path: Path):
    extract_dir = zip_path.parent
    with ZipFile(zip_path, 'r') as z:
        infos = z.filelist
        files = [info for info in infos if not info.is_dir()]
        if not files:
            raise RuntimeError(f'the archive "{str(zip_path.resolve())}" contains no files.')
        internal_path = Path(max(files, key=lambda info: info.file_size).filename)
        extracted_path = Path(z.extract(internal_path.as_posix(), extract_dir))

    zip_path.unlink(missing_ok=True)

    extracted_flat = extracted_path.name
    extracted_flat_path = extract_dir / extracted_flat

    if extracted_path != extracted_flat_path:
        extracted_path.replace(extracted_flat_path)
        extracted_path = extracted_flat_path

    if not extracted_path.replace(final_path).exists():
        if extracted_path.is_file():
            extracted_path.unlink(missing_ok=True)
        raise RuntimeError(f'failed to correctly extract the binary from archive "{zip_path.name}" to "{final_path}"')

    root_created_dir = extract_dir / internal_path.parts[0] if len(internal_path.parts) > 1 else None
    if root_created_dir and root_created_dir.exists():
        try:
            root_created_dir.rmdir()
        except OSError:
            pass


async def get_binary(bin_url: str, bin_path: Path, is_zipped: bool, force_update: bool = False) -> None:
    if is_binary_executable(bin_path) and not force_update:
        return

    orig_path = bin_path
    download_path = bin_path.with_suffix('.zip') if is_zipped else bin_path

    result = await download_file(
        bin_url,
        download_path,
        progress_callback=create_progress_bar(),
        logger=logger
    )

    if not result.success:
        download_path.unlink(missing_ok=True)
        raise RuntimeError(f'failed to load file from "{bin_url}": {result.error}')

    if is_zipped:
        unpack(result.file_path, orig_path)

    if not is_binary_executable(orig_path):
        download_path.unlink(missing_ok=True)
        raise RuntimeError(
            f'failed to install the executable file "{orig_path}" from "{bin_url}"'
        )

    if os_name != 'windows':
        mode = orig_path.stat().st_mode
        orig_path.chmod(mode | 0o111)


async def get_binaries_async(parallel: bool = False) -> None:
    tasks = [
        get_binary(
            bin_url=cfg['url'],
            bin_path=get_bin(name, as_str=False),
            is_zipped=cfg['is_zipped'],
        )
        for name, cfg in BINARIES.items()
    ]

    if parallel:
        await gather(*tasks)
    else:
        for task in tasks:
            await task


def extract_github_repo(url: str) -> str | None:
    """
    extract owner/repo from GitHub release URL.

    Example:
        'https://github.com/yt-dlp/yt-dlp/releases/...' -> 'yt-dlp/yt-dlp'
    """
    match = re_match(r'https://github\.com/([^/]+/[^/]+)/', url)
    return match.group(1) if match else None


async def get_release_date(repo: str) -> datetime | None:
    """
    fetch latest release published date from GitHub API.
    """
    api_url = f'https://api.github.com/repos/{repo}/releases/latest'
    data, result = await fetch_json(api_url, logger=logger)
    logger.info(f'  raw data type: {type(data)}')
    if result.success and data:
        if published := data.get('published_at'):
            # ISO format: "2024-01-15T10:30:00Z"
            return datetime.fromisoformat(published.replace('Z', '+00:00'))
    return None


def get_installed_date(path: Path) -> datetime | None:
    """
    get binary installation date from file modification time.
    """
    if path.exists():
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return None


async def is_update_available(url: str, bin_path: Path) -> bool:
    logger.info(f'checking update for: {bin_path}')

    installed_date = get_installed_date(bin_path)
    logger.info(f'  installed_date: {installed_date}')

    if not installed_date:
        logger.info(f'  → needs install (file missing)')
        return True

    repo = extract_github_repo(url)
    logger.info(f'  repo: {repo}')

    if not repo:
        logger.info(f'  → skip (not github)')
        return False

    release_date = await get_release_date(repo)
    logger.info(f'  release_date: {release_date}')

    if not release_date:
        logger.info(f'  → skip (no release date)')
        return False

    result = release_date > installed_date
    logger.info(f'  → needs_update: {result}')
    return result


async def update_binaries_async(parallel: bool = False, force: bool = False) -> dict[str, bool]:
    """
    check for updates and download newer versions of binaries.

    Args:
        parallel: run checks and downloads concurrently
        force: update all without checking release dates

    Returns:
        dict mapping binary name to whether it was updated
    """
    platform_bins = BINARIES
    results = {name: False for name in platform_bins}

    if not platform_bins:
        logger.warning(f'no binaries configured for platform: {os_name}')
        return results

    # determine what needs updating
    if force:
        to_update = list(platform_bins.keys())
    else:
        async def check(name: str, cfg: dict) -> tuple[str, bool]:
            return name, await is_update_available(cfg['url'], get_bin(name, as_str=False))

        if parallel:
            checks = await gather(*[check(n, c) for n, c in platform_bins.items()])
        else:
            checks = [await check(n, c) for n, c in platform_bins.items()]

        to_update = [name for name, needs in checks if needs]

    if not to_update:
        logger.info('all binaries are up to date')
        return results

    logger.info(f'updating binaries: {", ".join(to_update)}')

    # perform updates
    async def do_update(name: str) -> tuple[str, bool]:
        cfg = platform_bins[name]
        try:
            await get_binary(
                bin_url=cfg['url'],
                bin_path=get_bin(name, as_str=False),
                is_zipped=cfg['is_zipped'],
                force_update=True,
            )
            logger.info(f'{name}: updated successfully')
            return name, True
        except RuntimeError as e:
            logger.error(f'{name}: update failed - {e}')
            return name, False

    if parallel:
        outcomes = await gather(*[do_update(name) for name in to_update])
    else:
        outcomes = [await do_update(name) for name in to_update]

    for name, success in outcomes:
        results[name] = success

    return results


def run_async(coro) -> T:
    try:
        get_running_loop()
    except RuntimeError:
        return run(coro)

    result = None
    exception = None

    def thread_target():
        nonlocal result, exception
        try:
            result = run(coro)
        except BaseException as e:
            exception = e

    thread = Thread(target=thread_target)
    thread.start()
    thread.join()

    if exception is not None:
        raise exception
    return result


def get_binaries_sync(parallel: bool = False) -> dict[str, bool]:
    return run_async(get_binaries_async(parallel))


def update_binaries_sync(parallel: bool = False, force: bool = False) -> dict[str, bool]:
    return run_async(update_binaries_async(parallel, force))


class BackgroundUpdater:
    def __init__(self, update_interval: timedelta = timedelta(days=1)):
        self.update_interval = update_interval
        self.last_update_file = Path(".last_update")
        self._stop_event = Event()
        self._thread: Thread | None = None

    def _needs_update(self) -> bool:
        """checks if an update is needed"""
        if not self.last_update_file.exists():
            return True

        last_update = datetime.fromtimestamp(
            self.last_update_file.stat().st_mtime
        )
        return datetime.now() - last_update >= self.update_interval

    def _do_update(self):
        """performs an update"""
        try:
            logger.info(f'starting updating binaries...')
            update_binaries_sync()
            self.last_update_file.touch()
            logger.info(f'updating binaries... done')
        except Exception as e:
            logger.error(f'error updating binaries: {e}')

    def _run(self):
        """main background thread loop"""
        # Проверяем при старте
        if self._needs_update():
            self._do_update()

        # Периодическая проверка (каждый час)
        while not self._stop_event.wait(timeout=3600):
            if self._needs_update():
                self._do_update()

    def start(self):
        """starts background updating"""
        if self._thread is not None:
            return

        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info(f'background updating started')

    def stop(self):
        """stops background updating"""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
        logger.info(f'background updating stopped')


binaries_bg_updater = BackgroundUpdater(update_interval=timedelta(days=BINARIES_UPDATE_DAYS_INTERVAL))
yt_dlp_bin_str = get_bin('yt-dlp', as_str=True)
ffmpeg_bin_str = get_bin('ffmpeg', as_str=True)
bun_bin = get_bin('bun', as_str=False)
bun_bin_str = get_bin('bun', as_str=True)
