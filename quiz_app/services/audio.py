from pathlib import Path
from urllib.parse import parse_qs, urlparse

import yt_dlp


YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}
YOUTUBE_VIDEO_PATHS = ("/shorts/", "/live/", "/embed/")


def is_valid_youtube_url(video_url):
    """Return whether a URL identifies a supported YouTube video."""

    if not isinstance(video_url, str):
        return False
    parsed_url = urlparse(video_url)
    if not has_supported_youtube_host(parsed_url):
        return False
    return has_video_identifier(parsed_url)


def has_supported_youtube_host(parsed_url):
    """Return whether the parsed URL uses a supported YouTube host."""

    return (
        parsed_url.scheme in {"http", "https"}
        and parsed_url.netloc.lower() in YOUTUBE_HOSTS
    )


def has_video_identifier(parsed_url):
    """Return whether the parsed URL contains a video identifier."""

    if parsed_url.netloc.lower() == "youtu.be":
        return bool(parsed_url.path.strip("/"))
    if parsed_url.path == "/watch":
        return bool(parse_qs(parsed_url.query).get("v"))
    return any(
        parsed_url.path.removeprefix(video_path)
        for video_path in YOUTUBE_VIDEO_PATHS
        if parsed_url.path.startswith(video_path)
    )


def download_audio(video_url, audio_directory):
    """Download a YouTube video's audio track as an MP3 file."""

    if not is_valid_youtube_url(video_url):
        raise ValueError("A valid YouTube URL is required.")
    audio_directory.mkdir(parents=True, exist_ok=True)
    with yt_dlp.YoutubeDL(get_download_options(audio_directory)) as downloader:
        video_info = downloader.extract_info(video_url, download=True)
    return audio_directory / f"{video_info['id']}.mp3"


def get_download_options(audio_directory):
    """Return yt-dlp options for extracting MP3 audio."""

    return {
        "format": "bestaudio/best",
        "outtmpl": str(audio_directory / "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
    }
