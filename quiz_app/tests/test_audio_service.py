from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase
from yt_dlp.utils import DownloadError

from quiz_app.services.audio import download_audio, is_valid_youtube_url


class YouTubeUrlValidationTests(SimpleTestCase):
    def test_accepts_supported_youtube_urls(self):
        video_urls = [
            "https://www.youtube.com/watch?v=video123",
            "https://youtu.be/video123",
            "https://www.youtube.com/shorts/video123",
        ]
        for video_url in video_urls:
            with self.subTest(video_url=video_url):
                self.assertTrue(is_valid_youtube_url(video_url))

    def test_rejects_invalid_youtube_urls(self):
        video_urls = [
            "https://vimeo.com/video123",
            "https://www.youtube.com/watch",
            "https://www.youtube.com/shorts/",
            "not-a-url",
            None,
        ]
        for video_url in video_urls:
            with self.subTest(video_url=video_url):
                self.assertFalse(is_valid_youtube_url(video_url))


class AudioDownloadTests(SimpleTestCase):
    def assert_download_options(self, options, audio_directory):
        self.assertEqual(options["format"], "bestaudio/best")
        self.assertEqual(options["outtmpl"], str(audio_directory / "%(id)s.%(ext)s"))
        self.assertTrue(options["noplaylist"])
        self.assertTrue(options["quiet"])
        self.assertEqual(options["postprocessors"][0]["key"], "FFmpegExtractAudio")
        self.assertEqual(options["postprocessors"][0]["preferredcodec"], "mp3")
        self.assertEqual(options["postprocessors"][0]["preferredquality"], "192")

    def download_test_audio(self):
        with TemporaryDirectory() as temporary_directory:
            audio_directory = Path(temporary_directory) / "audio"
            audio_path = download_audio(
                "https://www.youtube.com/watch?v=video123",
                audio_directory,
            )
            self.assertTrue(audio_directory.exists())
        return audio_path, audio_directory

    def assert_download_call(self, downloader):
        self.assertEqual(downloader.extract_info.call_args.args, (
            "https://www.youtube.com/watch?v=video123",
        ))
        self.assertTrue(downloader.extract_info.call_args.kwargs["download"])

    @patch("quiz_app.services.audio.yt_dlp.YoutubeDL")
    def test_downloads_audio_as_mp3(self, youtube_dl_class):
        downloader = youtube_dl_class.return_value.__enter__.return_value
        downloader.extract_info.return_value = {"id": "video123"}
        audio_path, audio_directory = self.download_test_audio()
        self.assertEqual(audio_path.name, "video123.mp3")
        self.assert_download_options(youtube_dl_class.call_args.args[0], audio_directory)
        self.assert_download_call(downloader)

    @patch("quiz_app.services.audio.yt_dlp.YoutubeDL")
    def test_rejects_invalid_url_before_downloading(self, youtube_dl_class):
        with self.assertRaises(ValueError):
            download_audio("https://vimeo.com/video123", Path("audio"))
        youtube_dl_class.assert_not_called()

    @patch("quiz_app.services.audio.yt_dlp.YoutubeDL")
    def test_propagates_download_errors(self, youtube_dl_class):
        downloader = youtube_dl_class.return_value.__enter__.return_value
        downloader.extract_info.side_effect = DownloadError("Download failed")
        with TemporaryDirectory() as temporary_directory:
            with self.assertRaises(DownloadError):
                download_audio(
                    "https://www.youtube.com/watch?v=video123",
                    Path(temporary_directory),
                )
