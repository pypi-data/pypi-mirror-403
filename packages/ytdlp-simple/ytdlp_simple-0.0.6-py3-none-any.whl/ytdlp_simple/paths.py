from functools import lru_cache
from os import environ
from pathlib import Path
from tempfile import gettempdir

from ytdlp_simple.config import logger
from ytdlp_simple.config import os_name

LIB_DIR = Path(__file__).parent
PLUGINS_DIR = LIB_DIR / 'yt-dlp-plugins'


def _try_ctypes() -> str | None:
    try:
        import ctypes
    except ImportError:
        return None

    if not hasattr(ctypes, 'windll'):
        return None

    buf = ctypes.create_unicode_buffer(1024)
    ctypes.windll.shell32.SHGetFolderPathW(None, 28, None, 0, buf)  # 28 = CSIDL_LOCAL_APPDATA

    if not buf.value:
        return None

    if any(ord(c) > 255 for c in buf.value):
        buf2 = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.kernel32.GetShortPathNameW(buf.value, buf2, 1024):
            buf = buf2

    return buf.value


def _try_registry() -> str | None:
    try:
        import winreg

        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders',
        )
        value, _ = winreg.QueryValueEx(key, 'Local AppData')
        return str(value)
    except (ImportError, OSError):
        return None


@lru_cache(maxsize=1)
def user_data_dir() -> Path:
    path = ''
    if os_name == 'windows':
        path = _try_ctypes() or _try_registry() or environ.get('LOCALAPPDATA')
    elif os_name == 'linux':
        path = environ.get('XDG_DATA_HOME', '')
        if not path.strip():
            path = path.expanduser('~/.local/share')
    return Path(path).expanduser().resolve()


def is_writable_directory(folder: Path) -> bool:
    folder = Path(folder)
    if folder.is_file():
        return False
    try:
        folder.mkdir(parents=True, exist_ok=True)
        test_file = folder / '.write_test'
        test_file.touch(exist_ok=False)
        test_file.unlink()
        return True
    except Exception:
        return False


def get_tmp(lib_name: str):
    tmpdir = Path(gettempdir()) / lib_name
    tmpdir.mkdir(parents=True, exist_ok=True)
    return tmpdir


TMP_DIR = get_tmp(LIB_DIR.name)


@lru_cache(maxsize=4)
def get_out_dir(output_dir: Path | str | None = None) -> Path:
    """
    determines and creates a download directory
    """

    if output_dir:
        candidates = [Path(output_dir).resolve()]
    else:
        candidates = [
            Path.home() / 'Downloads' / 'ytdlp_downloads',
            Path.cwd() / 'ytdlp_downloads',
        ]

    for path in candidates:
        if is_writable_directory(path.parent):
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f'created the directory "{str(path)}"')
            return path

    raise RuntimeError(
        'FAILED to find a folder with write access permissions for downloading: '
        'manually specify a folder that is writable under the user account from which you are running the application!'
    )


plugins_dir_str = PLUGINS_DIR.resolve().as_posix()
tmp_dir_str = TMP_DIR.resolve().as_posix()

