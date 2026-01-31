from pathlib import Path
from typing import Literal

from ytdlp_simple.config import AUDIO_STREAM_PATTERN, VIDEO_STREAM_PATTERN, VIDEO_STREAM_PATTERN_ALT, DURATION_PATTERN, FPS_PATTERN, BITRATE_PATTERN
from ytdlp_simple.config import logger
from ytdlp_simple.type import MediaInfo
from ytdlp_simple.utils import run_subprocess
from ytdlp_simple.bins import ffmpeg_bin_str


async def get_media_info(file_path: Path | str) -> MediaInfo:
    """
    gets media file information via ffmpeg -i (stderr parsing),
    only the mp4 container provides complete information about bitrates:
    in mkv/webm, bitrates may be missing or incorrect.
    """
    file_path = Path(file_path).resolve()
    info = MediaInfo()

    if not file_path.exists():
        return info

    info.filesize = file_path.stat().st_size

    cmd = [ffmpeg_bin_str, '-hide_banner', '-i', file_path.as_posix()]
    _, _, stderr = await run_subprocess(cmd)

    # Duration: 00:00:47.51, start: 0.000000, bitrate: 312 kb/s
    duration_match = DURATION_PATTERN.search(stderr)
    if duration_match:
        h, m, s = duration_match.groups()
        info.duration = int(h) * 3600 + int(m) * 60 + float(s)

    bitrate_match = BITRATE_PATTERN.search(stderr)
    if bitrate_match:
        info.total_bitrate = int(bitrate_match.group(1))

    # Video: h264 (Main) (avc1 / 0x31637661), yuv420p(...), 360x640 [...], 258 kb/s, 30 fps
    video_match = VIDEO_STREAM_PATTERN.search(stderr, 2)
    if video_match:
        info.vcodec = video_match.group(1)
        info.width = int(video_match.group(2))
        info.height = int(video_match.group(3))
        if video_match.group(4):
            info.vbitrate = int(video_match.group(4))
        info.fps = float(video_match.group(5))
    else:
        # alternative pattern without bitrate
        video_alt = VIDEO_STREAM_PATTERN_ALT.search(stderr, 2)
        if video_alt:
            info.vcodec = video_alt.group(1)
            info.width = int(video_alt.group(2))
            info.height = int(video_alt.group(3))

        fps_alt = FPS_PATTERN.search(stderr)
        if fps_alt:
            info.fps = float(fps_alt.group(1))

    # Audio: aac (HE-AAC) (mp4a / 0x6134706D), 44100 Hz, stereo, fltp, 48 kb/s
    audio_match = AUDIO_STREAM_PATTERN.search(stderr, 2)
    if audio_match:
        info.acodec = audio_match.group(1)
        info.sample_rate = int(audio_match.group(2))
        info.channels = audio_match.group(3) or ''
        if audio_match.group(4):
            info.abitrate = int(audio_match.group(4))

    return info


async def ffmpeg_mux(
        video_path: Path | str,
        audio_path: Path | str,
        output_path: Path | str,
        delete_sources: bool = True,
) -> Path:
    """
    muxing video and audio in one container
    """
    video_path = Path(video_path).resolve()
    audio_path = Path(audio_path).resolve()
    output_path = Path(output_path).resolve()

    logger.info(f"muxing: {video_path.name} + {audio_path.name} -> {output_path.name}")

    cmd = [
        ffmpeg_bin_str,
        '-hide_banner',
        '-loglevel', 'warning',
        '-i', video_path.as_posix(),
        '-i', audio_path.as_posix(),
        '-c:v', 'copy',
        '-c:a', 'copy',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-sn', '-dn',
        '-map_metadata', '-1',
        '-map_chapters', '-1',
        '-movflags', '+faststart',
        '-y',
        output_path.as_posix(),
    ]

    returncode, stdout, stderr = await run_subprocess(cmd)

    if returncode != 0:
        logger.error(f'muxing failed: {stderr}')
        raise RuntimeError(f'FFmpeg muxing failed: {stderr}')

    if delete_sources:
        video_path.unlink(missing_ok=True)
        audio_path.unlink(missing_ok=True)

    logger.info(f'muxing complete: {output_path.name}')
    return output_path


async def ffmpeg_remux(file_path: Path | str, output_path: Path | str = None) -> Path:
    """
    remuxing mediafile for repair and compatibility:
    solves problems with playback in Telegram and other clients.
    """
    file_path = Path(file_path).resolve()

    if output_path:
        remuxed_path = Path(output_path).resolve()
    else:
        remuxed_path = file_path.with_stem(file_path.stem + '_remux')

    logger.info(f'remuxing: {file_path.name}')

    cmd = [
        ffmpeg_bin_str,
        '-hide_banner',
        '-loglevel', 'warning',
        '-i', file_path.as_posix(),
        '-c', 'copy',
        '-sn', '-dn',
        '-map_metadata', '-1',
        '-map_chapters', '-1',
        '-movflags', '+faststart',
        '-y',
        remuxed_path.as_posix(),
    ]

    returncode, stdout, stderr = await run_subprocess(cmd)

    if returncode != 0:
        logger.error(f'remuxing failed: {stderr}')
        raise RuntimeError(f'FFmpeg remuxing failed: {stderr}')

    # replacing the original if the path is not specified
    if not output_path and remuxed_path.is_file():
        file_path.unlink(missing_ok=True)
        remuxed_path.replace(file_path)
        logger.info(f'remuxing complete: {file_path.name}')
        return file_path

    logger.info(f'remuxing complete: {remuxed_path.name}')
    return remuxed_path


async def ffmpeg_audio_for_transcription(
        input_path: Path | str,
        output_path: Path | str = None,
        sample_rate: Literal[16000, 24000] = 16000,
        output_format: Literal['opus', 'flac', 'pcm'] = 'opus',
        delete_source: bool = True,
) -> Path:
    """
    prepares audio for transcription:
    - volume normalization by peaks
    - mixing to mono
    - resampling up to 16/24kHz
    - encoding in opus (24kbps speech) / flac / pcm
    """
    input_path = Path(input_path).resolve()

    if output_path:
        output_path = Path(output_path).resolve()
    else:
        output_path = input_path.with_stem(input_path.stem + '_transcription')

    if output_format == 'opus':
        output_path = output_path.with_suffix('.opus')
        codec_args = [
            '-c:a', 'libopus',
            '-b:a', '24k',
            '-application', 'voip',
            '-compression_level', '10',
            '-frame_duration', '20',
        ]
    elif output_format == 'flac':
        output_path = output_path.with_suffix('.flac')
        codec_args = [
            '-c:a', 'flac',
            '-compression_level', '12',
        ]
    else:  # pcm
        output_path = output_path.with_suffix('.wav')
        codec_args = ['-c:a', 'pcm_s16le']

    logger.info(f'processing audio for transcription: {input_path.name}')

    audio_filter = f'loudnorm=I=-16:TP=-1.5:LRA=11,aresample={sample_rate}:resampler=soxr'

    cmd = [
        ffmpeg_bin_str,
        '-hide_banner',
        '-loglevel', 'warning',
        '-i', input_path.as_posix(),
        '-vn',
        '-af', audio_filter,
        '-ac', '1',
        '-ar', str(sample_rate),
        *codec_args,
        '-y',
        output_path.as_posix(),
    ]

    returncode, stdout, stderr = await run_subprocess(cmd)

    if returncode != 0:
        logger.error(f'audio processing failed: {stderr}')
        raise RuntimeError(f'FFmpeg audio processing failed: {stderr}')

    if delete_source:
        input_path.unlink(missing_ok=True)

    logger.info(f'audio processing complete: {output_path.name}')
    return output_path
