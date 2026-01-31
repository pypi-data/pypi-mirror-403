from pathlib import Path
from typing import Literal
from uuid import uuid4

from ytdlp_simple.config import RESOLUTIONS, logger
from ytdlp_simple.paths import get_out_dir
from ytdlp_simple.ffmpeg import ffmpeg_audio_for_transcription, get_media_info, ffmpeg_remux
from ytdlp_simple.type import DownloadResult, VideoResolutions, AudioBitrates, VideoCodecs, AudioCodecs, SpeechLangs, MediaContainers
from ytdlp_simple.utils import create_task_dir, move_to_output, cleanup_task_dir, extract_yt_id, find_closest_resolution, get_container_compatibility
from ytdlp_simple.ytdlp import build_audio_format_selector, download_with_fallback, get_video_formats, analyze_available_formats, build_video_format_selector


from ytdlp_simple.bins import update_binaries_sync, binaries_bg_updater


update_binaries_sync()
binaries_bg_updater.start()


async def download_best_audio(
        url: str,
        output_dir: Path | str = None,
        prefer_lang: list[str] = None,
        sponsorblock: bool = True,
        cookies_folder: Path | str = None,
) -> DownloadResult:
    """
    downloads audio in maximum quality (opus with ~130 kbps bitrate)

    Args:
        url (str): video URL to download.
        output_dir (Path | str, optional): directory to save the result, default None (default directory used).
        prefer_lang (list[str], optional): prefer the languages of the audio, default ['ru', 'en'].
        sponsorblock (bool, optional): whether to remove (self-)advertising segments via SponsorBlock, default is True.
        cookies_folder (Path | str, optional): folder containing txt files with cookies in Netscape format, default None

    Returns:
        DownloadResult

            - success (bool): True if the download finished without errors.
            - path (Path | None): path to the saved file, or None on failure.
            - error (str | None): error message if the download failed.
            - warnings (list[str]): list of non‑critical warnings.
            - to_json() -> str: returns a JSON representation of the result, including all fields above.
    """
    out_dir = get_out_dir(output_dir)
    prefer_lang = prefer_lang or ['ru', 'en']
    task_dir = create_task_dir()

    try:
        format_string = build_audio_format_selector(
            prefer_codec='opus',
            quality='best',
            prefer_langs=prefer_lang,
        )

        # intermediate mp4 for correct metadata
        temp_template = (task_dir / '%(id)s.%(ext)s').resolve().as_posix()

        logger.info(f'downloading best audio: {url[:50]}...')

        result = await download_with_fallback(
            url=url,
            output_template=temp_template,
            format_string=format_string,
            cookies_folder=cookies_folder,
            extra_args=['-x', '--audio-quality', '0'],
            sponsorblock=sponsorblock,
            remux_after=True,
            task_dir=task_dir,
        )

        if result.success and result.path:
            final_path = move_to_output(result.path, out_dir)
            result.path = final_path

        return result

    finally:
        cleanup_task_dir(task_dir)


async def download_audio_for_transcription(
        url: str,
        output_dir: Path | str = None,
        cookies_folder: Path | str = None,
        sample_rate: Literal[16000, 24000] = 16000,
        output_format: Literal['opus', 'flac', 'pcm'] = 'opus',
        prefer_lang: list[str] = None,
) -> DownloadResult:
    """
    downloads low quality audio and prepares it for transcription.

    process: download low bitrate -> normalize -> mono -> resample -> encode


    Args:
        url (str): video URL to download.
        output_dir (Path | str, optional): directory to save the result, default None (default directory used).
        sample_rate: 16000 or 24000 Hz (for ASR models typically 16kHz)
        prefer_lang (list[str], optional): prefer the languages of the audio, default ['ru', 'en'].
        output_format: opus, flac or pcm (wav) - open formats uses in torchaudio/torchcodec/librosa/soundfile/etc
        cookies_folder (Path | str, optional): folder containing txt files with cookies in Netscape format, default None

    Returns:
        DownloadResult

            - success (bool): True if the download finished without errors.
            - path (Path | None): path to the saved file, or None on failure.
            - error (str | None): error message if the download failed.
            - warnings (list[str]): list of non‑critical warnings.
            - to_json() -> str: returns a JSON representation of the result, including all fields above.
    """
    out_dir = get_out_dir(output_dir)

    prefer_lang = prefer_lang or ['ru', 'en']
    task_dir = create_task_dir()

    try:
        format_string = build_audio_format_selector(
            prefer_codec='opus',
            quality='low',
            prefer_langs=prefer_lang,
        )

        video_id = extract_yt_id(url) or f'audio_{uuid4().hex[:8]}'
        temp_template = (task_dir / f'{video_id}_raw.%(ext)s').resolve().as_posix()

        logger.info(f'downloading audio for transcription: {url[:50]}...')

        result = await download_with_fallback(
            url=url,
            output_template=temp_template,
            format_string=format_string,
            cookies_folder=cookies_folder,
            extra_args=['-x'],
            sponsorblock=True,
            remux_after=False,
            task_dir=task_dir,
        )

        if not result.success:
            return result

        try:
            processed_path = await ffmpeg_audio_for_transcription(
                input_path=result.path,
                output_path=task_dir / f'{video_id}_transcription',
                sample_rate=sample_rate,
                output_format=output_format,
                delete_source=True,
            )

            final_path = move_to_output(processed_path, out_dir)

            return DownloadResult(success=True, path=final_path, warnings=result.warnings)

        except Exception as e:
            return DownloadResult(
                success=False,
                path=None,
                error=f'audio processing failed: {e}',
                warnings=result.warnings,
            )

    finally:
        cleanup_task_dir(task_dir)


async def download_video_for_chat(
        url: str,
        output_dir: Path | str = None,
        prefer_lang: list[str] = None,
        sponsorblock: bool = True,
        cookies_folder: Path | str = None,
) -> DownloadResult:
    """
    downloads video for chats/Telegram: 480p/360p, minimum audio bitrate, fps<=30,
    optimized for minimal size and traffic usage,
    correctly handles vertical videos (Shorts, Reels, TikTok).

    Args:
        url (str): video URL to download.
        output_dir (Path | str, optional): directory to save the result, default None (default directory used).
        prefer_lang (list[str], optional): prefer the languages of the audio, default ['ru', 'en'].
        sponsorblock (bool, optional): whether to remove (self-)advertising segments via SponsorBlock, default is True.
        cookies_folder (Path | str, optional): folder containing txt files with cookies in Netscape format, default None

    Returns:
        DownloadResult

            - success (bool): True if the download finished without errors.
            - path (Path | None): path to the saved file, or None on failure.
            - error (str | None): error message if the download failed.
            - warnings (list[str]): list of non‑critical warnings.
            - to_json() -> str: returns a JSON representation of the result, including all fields above.
    """
    out_dir = get_out_dir(output_dir)

    prefer_lang = prefer_lang or ['ru', 'en']
    task_dir = create_task_dir()
    warnings = []

    try:
        formats = await get_video_formats(url, cookies_folder=cookies_folder)
        available_resolutions = []
        orientation = 'unknown'

        if formats:
            analysis = analyze_available_formats(formats)
            available_resolutions = analysis.get('resolutions', [])
            orientation = analysis.get('orientation', 'unknown')
            logger.info(f'Video orientation: {orientation}, available resolutions: {available_resolutions}')

        # resolution: 480 -> 360 -> closest >= 360
        target_res = 480
        if available_resolutions:
            if 480 in available_resolutions:
                target_res = 480
            elif 360 in available_resolutions:
                target_res = 360
                warnings.append('480p unavailable, using 360p')
            else:
                suitable = [r for r in available_resolutions if r >= 360]
                if suitable:
                    target_res = min(suitable)
                    warnings.append(f'480p/360p unavailable, using {target_res}p')
                else:
                    target_res = max(available_resolutions) if available_resolutions else 480
                    warnings.append(f'no resolution >= 360p, using {target_res}p')

        # filter depending on orientation
        if orientation == 'vertical':
            # vertical: short side = width
            res_filter_exact = f'[width={target_res}]'
            res_filter_max = f'[width<={target_res}]'
            res_filter_min = '[width>=360]'
            alt_res_filter_exact = f'[height={target_res}]'
            alt_res_filter_max = f'[height<={target_res}]'
        elif orientation == 'horizontal':
            # horizontal: short side = height
            res_filter_exact = f'[height={target_res}]'
            res_filter_max = f'[height<={target_res}]'
            res_filter_min = '[height>=360]'
            alt_res_filter_exact = f'[width={target_res}]'
            alt_res_filter_max = f'[width<={target_res}]'
        else:
            # unknown: both options
            res_filter_exact = f'[height={target_res}]'
            res_filter_max = f'[height<={target_res}]'
            res_filter_min = '[height>=360]'
            alt_res_filter_exact = f'[width={target_res}]'
            alt_res_filter_max = f'[width<={target_res}]'
        # orientation-sensitive video selector
        video_selectors = []

        # first exact resolution with preferred codec
        for vcodec in ['vp9', 'avc']:
            video_selectors.append(f'bestvideo{res_filter_exact}[fps<=30][vcodec^={vcodec}]')
        video_selectors.append(f'bestvideo{res_filter_exact}[fps<=30]')
        video_selectors.append(f'bestvideo{res_filter_exact}')

        # alternative filter for unknown orientation
        if orientation == 'unknown':
            for vcodec in ['vp9', 'avc']:
                video_selectors.append(f'bestvideo{alt_res_filter_exact}[fps<=30][vcodec^={vcodec}]')
            video_selectors.append(f'bestvideo{alt_res_filter_exact}[fps<=30]')
            video_selectors.append(f'bestvideo{alt_res_filter_exact}')

        # limit by maximum
        for vcodec in ['vp9', 'avc']:
            video_selectors.append(f'bestvideo{res_filter_max}[fps<=30][vcodec^={vcodec}]')
        video_selectors.append(f'bestvideo{res_filter_max}[fps<=30]')
        video_selectors.append(f'bestvideo{res_filter_max}')

        # alternate maximum
        if orientation == 'unknown':
            video_selectors.append(f'bestvideo{alt_res_filter_max}[fps<=30]')
            video_selectors.append(f'bestvideo{alt_res_filter_max}')

        # min. 360p
        video_selectors.append(f'bestvideo{res_filter_min}[fps<=30]')
        video_selectors.append(f'bestvideo{res_filter_min}')

        # fallback
        video_selectors.append('bestvideo[fps<=30]')
        video_selectors.append('bestvideo')

        # minimum audio bitrate (usually: he-aac with sbr)
        audio_selectors = []
        for lang in prefer_lang:
            audio_selectors.append(f'worstaudio[acodec^=mp4a][language^={lang}]')
        audio_selectors.append('worstaudio[acodec^=mp4a]')
        for lang in prefer_lang:
            audio_selectors.append(f'worstaudio[language^={lang}]')
        audio_selectors.append('worstaudio')

        format_string = f'({'/'.join(video_selectors)})+({'/'.join(audio_selectors)})/best[height<=480]/best'

        temp_template = (task_dir / '%(id)s.%(ext)s').resolve().as_posix()

        logger.info(f'downloading video for chat ({target_res}p, {orientation}): {url[:50]}...')

        result = await download_with_fallback(
            url=url,
            output_template=temp_template,
            format_string=format_string,
            cookies_folder=cookies_folder,
            extra_args=[
                '--merge-output-format', 'mp4',
                '--remux-video', 'mp4',
            ],
            sponsorblock=sponsorblock,
            remux_after=True,
            task_dir=task_dir,
        )

        if result.success and result.path:
            # checking downloaded video parameters
            info = await get_media_info(result.path)

            if info.width > 0 and info.height > 0:
                actual_short_side = min(info.width, info.height)
                actual_orientation = 'vertical' if info.height > info.width else 'horizontal'

                logger.info(f'downloaded: {info.width}x{info.height} ({actual_orientation}), '
                            f'short side: {actual_short_side}p, audio: {info.abitrate}kb/s')

                if actual_short_side > target_res * 1.15:
                    warnings.append(f'got {actual_short_side}p instead of {target_res}p')

            final_path = move_to_output(result.path, out_dir)
            result.path = final_path

        result.warnings.extend(warnings)
        return result

    finally:
        cleanup_task_dir(task_dir)


async def download_best_quality(
        url: str,
        output_dir: Path | str = None,
        prefer_lang: list[str] = None,
        sponsorblock: bool = True,
        cookies_folder: Path | str = None,
        container: MediaContainers = 'mp4',
) -> DownloadResult:
    """
    downloads videos in maximum quality: best video (vp9) + best audio (opus).

    Args:
        url (str): video URL to download.
        output_dir (Path | str, optional): directory to save the result, default None (default directory used).
        prefer_lang (list[str], optional): prefer the languages of the audio, default ['ru', 'en'].
        sponsorblock (bool, optional): whether to remove (self-)advertising segments via SponsorBlock, default is True.
        cookies_folder (Path | str, optional): folder containing txt files with cookies in Netscape format, default None
        container (MediaContainers, optional): media container type (mp4, mkv, webm, mov), default 'mp4'.

    Returns:
        DownloadResult

            - success (bool): True if the download finished without errors.
            - path (Path | None): path to the saved file, or None on failure.
            - error (str | None): error message if the download failed.
            - warnings (list[str]): list of non‑critical warnings.
            - to_json() -> str: returns a JSON representation of the result, including all fields above.
    """
    out_dir = get_out_dir(output_dir)

    prefer_lang = prefer_lang or ['ru', 'en']
    task_dir = create_task_dir()

    try:
        video_selectors = [
            'bestvideo[vcodec^=vp9]',
            'bestvideo[vcodec^=av01]',
            'bestvideo[vcodec^=avc]',
            'bestvideo',
        ]

        audio_format = build_audio_format_selector(
            prefer_codec='opus',
            quality='best',
            prefer_langs=prefer_lang,
        )

        format_string = f'({'/'.join(video_selectors)})+({audio_format})/best'

        # temporary in mp4 for metadata, then remux in the target container
        temp_template = (task_dir / '%(id)s.mp4').resolve().as_posix()

        logger.info(f'downloading best quality: {url[:50]}...')

        result = await download_with_fallback(
            url=url,
            output_template=temp_template,
            format_string=format_string,
            cookies_folder=cookies_folder,
            extra_args=['--merge-output-format', 'mp4'],
            sponsorblock=sponsorblock,
            remux_after=True,
            task_dir=task_dir,
        )

        if result.success and result.path:
            # remux into target container if necessary
            if container != 'mp4':
                target_path = result.path.with_suffix(f'.{container}')
                await ffmpeg_remux(result.path, target_path)
                result.path.unlink(missing_ok=True)
                result.path = target_path

            final_path = move_to_output(result.path, out_dir)
            result.path = final_path

        return result

    finally:
        cleanup_task_dir(task_dir)


async def download_manual(
        url: str,
        output_dir: Path | str = None,
        max_resolution: VideoResolutions = '4k',
        audio_bitrate: AudioBitrates = 'best',
        vcodec: VideoCodecs = 'avc',
        acodec: AudioCodecs = 'opus',
        speech_lang: SpeechLangs = 'ru',
        limit_fps: bool = False,
        container: MediaContainers = 'mp4',
        sponsorblock: bool = True,
        cookies_folder: Path | str = None,
) -> DownloadResult:
    """
    manual parameters choice

    Args:
        url (str): video URL to download.
        output_dir (Path | str, optional): directory to save the result, default None (default directory used).
        max_resolution: '8k'-'144p'
        audio_bitrate: 'best'/'medium'/'low'
        vcodec: 'av1'/'vp9'/'avc'/'hevc'
        acodec: 'opus'/'aac'
        speech_lang: 'orig'/'ru'/'en' (orig = no language filter)
        limit_fps: limit to 30fps
        container (MediaContainers, optional): media container type (mp4, mkv, webm, mov), default 'mp4'.
        sponsorblock (bool, optional): whether to remove (self-)advertising segments via SponsorBlock, default is True.
        cookies_folder: folder containing txt files with cookies in Netscape format

    Returns:
        DownloadResult

            - success (bool): True if the download finished without errors.
            - path (Path | None): path to the saved file, or None on failure.
            - error (str | None): error message if the download failed.
            - warnings (list[str]): list of non‑critical warnings.
            - to_json() -> str: returns a JSON representation of the result, including all fields above.
    """
    out_dir = get_out_dir(output_dir)

    warnings = []
    target_height = RESOLUTIONS.get(max_resolution, 1080)
    task_dir = create_task_dir()

    try:
        # get available formats
        formats = await get_video_formats(url, cookies_folder=cookies_folder)
        available_heights = []
        orientation = 'unknown'
        if formats:
            analysis = analyze_available_formats(formats)
            available_resolutions = analysis.get('resolutions', [])  # short side filtration
            orientation = analysis.get('orientation', 'unknown')
            logger.info(f'video orientation: {orientation}')
            if available_resolutions:
                actual_res = find_closest_resolution(target_height, available_resolutions, prefer_lower=True)
                if actual_res != target_height:
                    warnings.append(f'Resolution {max_resolution} unavailable, using {actual_res}p')
                    target_height = actual_res
            # check the availability of codecs
            available_vcodecs = analysis.get('vcodecs', set())
            vcodec_map = {'av1': 'av01', 'vp9': 'vp9', 'avc': 'avc', 'hevc': 'hvc'}
            if vcodec_map.get(vcodec, vcodec) not in ' '.join(available_vcodecs):
                if 'vp9' in ' '.join(available_vcodecs):
                    warnings.append(f'codec {vcodec} unavailable, using vp9')
                    vcodec = 'vp9'
                elif 'avc' in ' '.join(available_vcodecs) or 'h264' in ' '.join(available_vcodecs):
                    warnings.append(f'codec {vcodec} unavailable, using avc')
                    vcodec = 'avc'

        # check container compatibility
        compat = get_container_compatibility(container)

        vcodec_compat = {'av1': 'av01', 'vp9': 'vp9', 'avc': 'h264', 'hevc': 'hevc'}
        if vcodec_compat.get(vcodec, vcodec) not in ' '.join(compat['video']):
            if container == 'webm':
                container = 'mkv'
                warnings.append(f'container webm incompatible with {vcodec}, using mkv')
            elif container == 'mov' and vcodec in ['vp9', 'av1']:
                container = 'mp4'
                warnings.append(f'container mov incompatible with {vcodec}, using mp4')

        acodec_compat = {'opus': 'opus', 'aac': 'aac'}
        if acodec_compat.get(acodec, acodec) not in ' '.join(compat['audio']):
            if container == 'webm' and acodec == 'aac':
                container = 'mp4'
                warnings.append(f'container webm incompatible with {acodec}, using mp4')

        # language preferences
        prefer_langs = []
        if speech_lang == 'ru':
            prefer_langs = ['ru', 'en']
        elif speech_lang == 'en':
            prefer_langs = ['en', 'ru']
        # orig = empty list w/o filter

        # format selectors
        video_format = build_video_format_selector(
            max_height=target_height,
            prefer_codec=vcodec, # noqa
            limit_fps=limit_fps,
            available_heights=available_heights,
            orientation=orientation # noqa
        )

        audio_format = build_audio_format_selector(
            prefer_codec=acodec,
            quality=audio_bitrate,
            prefer_langs=prefer_langs if prefer_langs else None,
        )

        format_string = f'({video_format})+({audio_format})/best'

        # temporary always mp4 for correct metadata
        temp_template = (task_dir / '%(id)s.mp4').resolve().as_posix()

        logger.info(f'downloading: {max_resolution}, {vcodec}, {acodec}, lang={speech_lang}, fps_limit={limit_fps}')

        result = await download_with_fallback(
            url=url,
            output_template=temp_template,
            format_string=format_string,
            cookies_folder=cookies_folder,
            extra_args=['--merge-output-format', 'mp4'],
            sponsorblock=sponsorblock,
            remux_after=True,
            task_dir=task_dir,
        )

        if result.success and result.path:
            # check the actual parameters
            info = await get_media_info(result.path)

            if info.height > 0:
                actual_short_side = min(info.width, info.height)
                if actual_short_side > target_height * 1.15:
                    warnings.append(f'Got {actual_short_side}p instead of {target_height}p')

            if info.vcodec and vcodec.lower() not in info.vcodec.lower():
                if not (vcodec in ['avc', 'h264'] and info.vcodec.lower() in ['h264', 'avc']):
                    warnings.append(f'Got codec {info.vcodec} instead of {vcodec}')

            if limit_fps and info.fps > 35:
                warnings.append(f'got {info.fps:.0f}fps despite limit_fps=True')

            if info.abitrate > 0:
                logger.info(f'audio bitrate: {info.abitrate} kb/s')

            # remux into target container
            if container != 'mp4':
                target_path = result.path.with_suffix(f'.{container}')
                try:
                    await ffmpeg_remux(result.path, target_path)
                    result.path.unlink(missing_ok=True)
                    result.path = target_path
                except Exception as e:
                    warnings.append(f'remux to {container} failed: {e}, keeping mp4')

            final_path = move_to_output(result.path, out_dir)
            result.path = final_path

        result.warnings.extend(warnings)

        for w in warnings:
            logger.warning(w)

        return result

    finally:
        cleanup_task_dir(task_dir)
