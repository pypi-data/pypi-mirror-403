import platform
import re

from ytdlp_simple.log import setup_logger

os_name = platform.system().lower()

logger = setup_logger(
    name='YTDLP_SIMPLE',
    level='INFO',
    log_file=None,
    datefmt='%d.%m.%Y %H:%M:%S',
    logfmt='%(asctime)s [%(name)s] | %(levelname)s: %(message)s'
)

# invidious instances
INVIDIOUS_INSTANCES = [
    'yewtu.be',
    'invidious.nerdvpn.de',
]

# frame resolutions mapping
RESOLUTIONS = {
    '8k': 4320, '4k': 2160, '2k': 1440,
    '1080p': 1080, '720p': 720, '540p': 540,
    '480p': 480, '360p': 360, '240p': 240, '144p': 144,
}

RESOLUTION_NAMES = {v: k for k, v in RESOLUTIONS.items()}

YT_ID_PATTERN = re.compile(
    r'(?:https?://)?(?:www\.)?(?:youtube|youtu|youtube-nocookie)\.(?:com|be)/'
    r'(?:watch\?v=|embed/|v/|.+\?v=|shorts/)?'
    r'([^&=%?\s]{11})'
)
VIDEO_STREAM_PATTERN = re.compile(r'Stream\s+#\d+:\d+.*?Video:\s*(\w+).*?(\d+)x(\d+).*?(?:(\d+)\s*kb/s)?.*?(\d+(?:\.\d+)?)\s*fps')
VIDEO_STREAM_PATTERN_ALT = re.compile(r'Stream\s+#\d+:\d+.*?Video:\s*(\w+).*?(\d+)x(\d+)')
AUDIO_STREAM_PATTERN = re.compile(r'Stream\s+#\d+:\d+.*?Audio:\s*(\w+(?:[- ]\w+)?).*?(\d+)\s*Hz,?\s*(\w+)?.*?(?:(\d+)\s*kb/s)?')
DURATION_PATTERN = re.compile(r'Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)')
FPS_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*fps')
BITRATE_PATTERN = re.compile(r'bitrate:\s*(\d+)\s*kb/s')


BINARIES_SOURCES = {
    'linux': {
        'ffmpeg': {'url': 'https://github.com/imbecility/ffmpeg-ytdlp-minimal/releases/latest/download/ffmpeg-linux64', 'is_zipped': False},
        'ffprobe': {'url': 'https://github.com/imbecility/ffmpeg-ytdlp-minimal/releases/latest/download/ffprobe-linux64', 'is_zipped': False},
        'bun': {'url': 'https://github.com/oven-sh/bun/releases/latest/download/bun-linux-x64.zip', 'is_zipped': True},
        'yt-dlp': {'url': 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux', 'is_zipped': False},
    },
    'windows': {
        'ffmpeg': {'url': 'https://github.com/imbecility/ffmpeg-ytdlp-minimal/releases/latest/download/ffmpeg-win64.exe', 'is_zipped': False},
        'ffprobe': {'url': 'https://github.com/imbecility/ffmpeg-ytdlp-minimal/releases/latest/download/ffprobe-win64.exe', 'is_zipped': False},
        'bun': {'url': 'https://github.com/oven-sh/bun/releases/latest/download/bun-windows-x64.zip', 'is_zipped': True},
        'yt-dlp': {'url': 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe', 'is_zipped': False},
    },
}

BINARIES_UPDATE_DAYS_INTERVAL = 1
