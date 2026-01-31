from json import loads as json_loads, JSONDecodeError
from pathlib import Path

from ytdlp_simple.config import INVIDIOUS_INSTANCES, logger
from ytdlp_simple.ffmpeg import ffmpeg_remux
from ytdlp_simple.type import FormatInfo, DownloadResult, FrameOrientations, AudioQuality, AudioCodecs, VideoCodecs
from ytdlp_simple.utils import run_subprocess, find_closest_resolution, create_task_dir, extract_yt_id, get_invidious_url, get_cookie_arg
from ytdlp_simple.paths import PLUGINS_DIR, tmp_dir_str, plugins_dir_str
from ytdlp_simple.bins import yt_dlp_bin_str, ffmpeg_bin_str, bun_bin_str, bun_bin

def base_ytdlp_cmd(cookies_folder: Path | str, sponsorblock: bool = True) -> list[str]:
    """basic arguments for yt-dlp"""
    cmd = [yt_dlp_bin_str]
    cmd.extend(get_cookie_arg(cookies_folder))

    cmd.extend([
        '--cache-dir', tmp_dir_str,
        # '--rm-cache-dir',
        '--no-abort-on-error',
        '--windows-filenames',
        '--no-part',
        '--no-write-thumbnail',
        '--no-write-comments',
        '--force-overwrites',  # overwrite existing files
        '--extractor-retries', '3',
        '--file-access-retries', '3',
        '--fragment-retries', '5',
        '--retry-sleep', 'exp=1:5',
        '--ffmpeg-location', ffmpeg_bin_str,
        '--concurrent-fragments', '5',
    ])

    if PLUGINS_DIR.exists() and any(PLUGINS_DIR.iterdir()):
        cmd.extend(['--plugin-dirs', plugins_dir_str])

    if bun_bin.exists():
        cmd.extend(['--js-runtimes', f'bun:{bun_bin_str}'])

    if sponsorblock:
        cmd.extend(['--sponsorblock-remove', 'all'])

    return cmd


async def get_video_formats(url: str, cookies_folder: Path | str) -> list[FormatInfo] | None:
    """
    retrieves information about available video formats.
    useful for smart format selection and API.

    Returns:
        list of FormatInfo or None in case of an error
    """
    cmd = base_ytdlp_cmd(cookies_folder, sponsorblock=False) + [
        '-J',
        '--no-download',
        url
    ]

    returncode, stdout, stderr = await run_subprocess(cmd)

    if returncode != 0:
        logger.warning(f'Failed to get video info: {stderr[:200]}')
        return None

    try:
        data = json_loads(stdout)
        formats = []

        for fmt in data.get('formats', []):
            info = FormatInfo(
                format_id=fmt.get('format_id', ''),
                ext=fmt.get('ext', ''),
                height=fmt.get('height') or 0,
                width=fmt.get('width') or 0,
                fps=fmt.get('fps') or 0,
                vcodec=fmt.get('vcodec', 'none'),
                acodec=fmt.get('acodec', 'none'),
                vbr=fmt.get('vbr') or 0,
                abr=fmt.get('abr') or 0,
                filesize=fmt.get('filesize') or fmt.get('filesize_approx') or 0,
                language=fmt.get('language') or '',
                quality_note=fmt.get('format_note', ''),
            )
            formats.append(info)

        return formats
    except JSONDecodeError:
        logger.error('Failed to parse video info JSON')
        return None


def analyze_available_formats(formats: list[FormatInfo]) -> dict:
    """
    analyze formats and returns statistics, including orientation
    """
    if not formats:
        return {}

    video_formats = [f for f in formats if f.vcodec != 'none']
    audio_formats = [f for f in formats if f.acodec != 'none' and f.vcodec == 'none']

    # collect permissions along the SHORT side
    available_resolutions = sorted(set(
        min(f.width, f.height) for f in video_formats if f.width > 0 and f.height > 0
    ))

    # and heights for compatibility
    available_heights = sorted(set(f.height for f in video_formats if f.height > 0))

    orientation = determine_orientation(formats)

    return {
        'resolutions': available_resolutions,
        'heights': available_heights,
        'fps_options': sorted(set(f.fps for f in video_formats if f.fps > 0)),
        'vcodecs': set(f.vcodec.split('.')[0] for f in video_formats if f.vcodec != 'none'),
        'acodecs': set(f.acodec.split('.')[0] for f in audio_formats if f.acodec != 'none'),
        'languages': set(f.language for f in audio_formats if f.language),
        'orientation': orientation,
        'video_count': len(video_formats),
        'audio_count': len(audio_formats),
    }


def build_audio_format_selector(
        prefer_codec: AudioCodecs = 'opus',
        quality: AudioQuality = 'best',
        prefer_langs: list[str] = None,
) -> str:
    """
    builds format selector for audio

    quality:
        - 'best': maximum bitrate (bestaudio)
        - 'medium': average bitrate (bestaudio filtered by format_note)
        - 'low': minimal bitrate (worstaudio)
    """
    prefer_langs = prefer_langs or ['ru', 'en']

    # basic selector depending on quality
    if quality == 'low':
        base_selector = 'worstaudio'
    else:
        base_selector = 'bestaudio'

    codec_map = {'opus': 'opus', 'aac': 'mp4a'}
    codec_pattern = codec_map.get(prefer_codec, prefer_codec)

    selectors = []

    if quality == 'medium':
        for lang in prefer_langs:
            selectors.append(f'bestaudio[acodec^={codec_pattern}][language^={lang}][format_note*=medium]')
        selectors.append(f'bestaudio[acodec^={codec_pattern}][format_note*=medium]')
        for lang in prefer_langs:
            selectors.append(f'bestaudio[language^={lang}][format_note*=medium]')
        selectors.append('bestaudio[format_note*=medium]')

    for lang in prefer_langs:
        selectors.append(f'{base_selector}[acodec^={codec_pattern}][language^={lang}]')
    selectors.append(f'{base_selector}[acodec^={codec_pattern}]')
    for lang in prefer_langs:
        selectors.append(f'{base_selector}[language^={lang}]')
    selectors.append(base_selector)

    return '/'.join(selectors)


def determine_orientation(formats: list[FormatInfo]) -> FrameOrientations:
    """
    determine the video orientation based on available formats
    """
    if not formats:
        return 'unknown'

    video_formats = [f for f in formats if f.vcodec != 'none' and f.width > 0 and f.height > 0]
    if not video_formats:
        return 'unknown'

    vertical_count = sum(1 for f in video_formats if f.height > f.width)
    horizontal_count = sum(1 for f in video_formats if f.width >= f.height)

    if vertical_count > 0 and horizontal_count == 0:
        return 'vertical'
    elif horizontal_count > 0 and vertical_count == 0:
        return 'horizontal'
    elif vertical_count > 0 and horizontal_count > 0:
        return 'mixed'
    return 'unknown'


def build_video_format_selector(
        max_height: int = 1080,
        min_height: int = 0,
        prefer_codec: VideoCodecs = 'avc',
        limit_fps: bool = True,
        available_heights: list[int] = None,
        orientation: FrameOrientations = 'unknown',
) -> str:
    """
    builds format selector for videos,
    for vertical videos resolution = width, not height
    """
    if available_heights:
        actual_height = find_closest_resolution(max_height, available_heights, prefer_lower=True)
        if actual_height != max_height:
            logger.info(f'Resolution {max_height}p unavailable, using {actual_height}p')
        max_height = actual_height

    codec_map = {
        'av1': 'av01', 'vp9': 'vp9',
        'avc': 'avc|h264', 'h264': 'avc|h264',
        'hevc': 'hvc|h265|hevc', 'h265': 'hvc|h265|hevc',
    }
    codec_pattern = codec_map.get(prefer_codec, 'avc|h264')
    fps_filter = '[fps<=30]' if limit_fps else ''

    selectors = []

    # filters according to orientation
    if orientation == 'vertical':
        # for vertical: the short side = width
        size_filter = f'[width<={max_height}]'
        exact_filter = f'[width={max_height}]'
        min_filter = f'[width>={min_height}]' if min_height > 0 else ''
    elif orientation == 'horizontal':
        # for horizontal: short side = height
        size_filter = f'[height<={max_height}]'
        exact_filter = f'[height={max_height}]'
        min_filter = f'[height>={min_height}]' if min_height > 0 else ''
    else:
        # unknown/mixed - fallback chain for both options
        size_filter = f'[height<={max_height}]'
        exact_filter = f'[height={max_height}]'
        alt_size_filter = f'[width<={max_height}]'
        alt_exact_filter = f'[width={max_height}]'
        min_filter = f'[height>={min_height}]' if min_height > 0 else ''

        # first horizontal filters, then vertical
        selectors.extend([
            # horizontal
            f'bestvideo{exact_filter}{fps_filter}[vcodec~="^({codec_pattern})"]',
            f'bestvideo{exact_filter}{fps_filter}',
            f'bestvideo{size_filter}{fps_filter}[vcodec~="^({codec_pattern})"]',
            f'bestvideo{size_filter}{fps_filter}',
            # vertical (fallback)
            f'bestvideo{alt_exact_filter}{fps_filter}[vcodec~="^({codec_pattern})"]',
            f'bestvideo{alt_exact_filter}{fps_filter}',
            f'bestvideo{alt_size_filter}{fps_filter}[vcodec~="^({codec_pattern})"]',
            f'bestvideo{alt_size_filter}{fps_filter}',
            # w/o fps limit
            f'bestvideo{size_filter}[vcodec~="^({codec_pattern})"]',
            f'bestvideo{size_filter}',
            f'bestvideo{alt_size_filter}[vcodec~="^({codec_pattern})"]',
            f'bestvideo{alt_size_filter}',
        ])

        if min_height > 0:
            selectors.append(f'bestvideo{min_filter}')
        selectors.append('bestvideo')

        return '/'.join(selectors)

    # standard selectors set for a known orientation
    selectors = [
        f'bestvideo{exact_filter}{fps_filter}[vcodec~="^({codec_pattern})"]',
        f'bestvideo{exact_filter}{fps_filter}',
        f'bestvideo{exact_filter}',
        f'bestvideo{size_filter}{fps_filter}[vcodec~="^({codec_pattern})"]',
        f'bestvideo{size_filter}{fps_filter}',
        f'bestvideo{size_filter}[vcodec~="^({codec_pattern})"]',
        f'bestvideo{size_filter}',
    ]

    if min_filter:
        selectors.append(f'bestvideo{min_filter}')
    selectors.append('bestvideo')

    return '/'.join(selectors)


async def download_with_fallback(
        url: str,
        output_template: str,
        format_string: str,
        cookies_folder: Path | str = None,
        extra_args: list[str] = None,
        sponsorblock: bool = True,
        remux_after: bool = True,
        use_invidious_fallback: bool = True,
        task_dir: Path = None,
) -> DownloadResult:
    """
    downloads videos from YouTube with a fallback to Invidious.
    uses a unique task directory for isolation.
    """
    result = DownloadResult(success=False, path=None, error=None)
    extra_args = extra_args or []
    warnings = []

    own_task_dir = task_dir is None
    if own_task_dir:
        task_dir = create_task_dir()

    try:
        cmd = base_ytdlp_cmd(cookies_folder, sponsorblock=sponsorblock) + [
            '-f', format_string,
            '-o', output_template,
            '--print', 'after_move:filepath',
            *extra_args,
            url
        ]
        logger.debug(f'running `{cmd}`')
        returncode, stdout, stderr = await run_subprocess(cmd)

        # invidious fallback
        if returncode != 0 and use_invidious_fallback:
            video_id = extract_yt_id(url)
            if video_id:
                logger.warning('YouTube download failed, trying Invidious fallback...')
                warnings.append(f'original YouTube failed: {stderr[:100]}')

                for instance in INVIDIOUS_INSTANCES:
                    invidious_url = get_invidious_url(video_id, instance)
                    cmd[-1] = invidious_url

                    returncode, stdout, stderr = await run_subprocess(cmd)
                    if returncode == 0:
                        logger.info(f'downloaded via Invidious ({instance})')
                        warnings.append(f'used Invidious: {instance}')
                        break

        if returncode != 0:
            result = DownloadResult(
                success=False,
                path=None,
                error=f'download failed: {stderr[:500]}',
                warnings=warnings
            )
            return result

        # parse file path
        filepath = None
        for line in stdout.strip().split('\n'):
            line = line.strip()
            if line and Path(line).exists():
                filepath = line
                break

        if not filepath:
            # search by pattern
            for f in sorted(task_dir.glob('*'), key=lambda x: x.stat().st_mtime, reverse=True):
                if f.is_file() and f.suffix in ['.mp4', '.mkv', '.webm', '.m4a', '.opus', '.mp3', '.wav', '.ogg']:
                    filepath = str(f)
                    break

        if not filepath or not Path(filepath).exists():
            result = DownloadResult(
                success=False,
                path=None,
                error='could not find downloaded file',
                warnings=warnings
            )
            return result

        result_path = Path(filepath)

        # remux
        if remux_after:
            try:
                result_path = await ffmpeg_remux(result_path)
            except Exception as e:
                logger.warning(f'remux failed: {e}')
                warnings.append(f'remux skipped: {e}')

        result = DownloadResult(success=True, path=result_path, warnings=warnings)
        return result

    finally:
        logger.debug(f'finished downloading task {task_dir.name}:\n{result.to_json()}')
