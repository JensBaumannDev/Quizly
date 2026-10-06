from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.test import SimpleTestCase

from quiz_app.services.transcription import load_whisper_model, transcribe_audio


class AudioTranscriptionTests(SimpleTestCase):
    def create_audio_file(self, directory):
        audio_path = Path(directory) / "video.mp3"
        audio_path.touch()
        return audio_path

    @patch("quiz_app.services.transcription.import_module")
    def test_loads_base_whisper_model(self, import_module):
        model = load_whisper_model()
        import_module.assert_called_once_with("whisper")
        import_module.return_value.load_model.assert_called_once_with("base")
        self.assertEqual(model, import_module.return_value.load_model.return_value)

    @patch("quiz_app.services.transcription.import_module")
    def test_propagates_whisper_loading_errors(self, import_module):
        import_module.side_effect = ImportError("Whisper unavailable")
        with self.assertRaises(ImportError):
            load_whisper_model()

    @patch("quiz_app.services.transcription.load_whisper_model")
    def test_transcribes_existing_audio_file(self, load_model):
        model = load_model.return_value
        model.transcribe.return_value = {"text": "  Python basics  "}
        with TemporaryDirectory() as temporary_directory:
            audio_path = self.create_audio_file(temporary_directory)
            transcript = transcribe_audio(audio_path)
        self.assertEqual(transcript, "Python basics")
        load_model.assert_called_once_with()
        model.transcribe.assert_called_once_with(str(audio_path))

    @patch("quiz_app.services.transcription.load_whisper_model")
    def test_rejects_missing_audio_file(self, load_model):
        with self.assertRaises(FileNotFoundError):
            transcribe_audio(Path("missing.mp3"))
        load_model.assert_not_called()

    @patch("quiz_app.services.transcription.load_whisper_model")
    def test_rejects_directory_as_audio_file(self, load_model):
        with TemporaryDirectory() as temporary_directory:
            with self.assertRaises(FileNotFoundError):
                transcribe_audio(temporary_directory)
        load_model.assert_not_called()

    @patch("quiz_app.services.transcription.load_whisper_model")
    def test_rejects_empty_transcript(self, load_model):
        load_model.return_value.transcribe.return_value = {"text": "  "}
        with TemporaryDirectory() as temporary_directory:
            audio_path = self.create_audio_file(temporary_directory)
            with self.assertRaises(ValueError):
                transcribe_audio(audio_path)

    @patch("quiz_app.services.transcription.load_whisper_model")
    def test_rejects_missing_transcript_text(self, load_model):
        load_model.return_value.transcribe.return_value = {}
        with TemporaryDirectory() as temporary_directory:
            audio_path = self.create_audio_file(temporary_directory)
            with self.assertRaises(ValueError):
                transcribe_audio(audio_path)

    @patch("quiz_app.services.transcription.load_whisper_model")
    def test_rejects_invalid_whisper_results(self, load_model):
        invalid_results = [None, [], {"text": None}, {"text": 123}]
        with TemporaryDirectory() as temporary_directory:
            audio_path = self.create_audio_file(temporary_directory)
            for result in invalid_results:
                with self.subTest(result=result), self.assertRaises(ValueError):
                    load_model.return_value.transcribe.return_value = result
                    transcribe_audio(audio_path)

    @patch("quiz_app.services.transcription.load_whisper_model")
    def test_propagates_transcription_errors(self, load_model):
        load_model.return_value.transcribe.side_effect = RuntimeError("Failed")
        with TemporaryDirectory() as temporary_directory:
            audio_path = self.create_audio_file(temporary_directory)
            with self.assertRaises(RuntimeError):
                transcribe_audio(audio_path)
