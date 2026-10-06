from importlib import import_module
from pathlib import Path


WHISPER_MODEL = "base"


def transcribe_audio(audio_path):
    audio_path = Path(audio_path)
    if not audio_path.is_file():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    model = load_whisper_model()
    result = model.transcribe(str(audio_path))
    return extract_transcript(result)


def extract_transcript(result):
    transcript = result.get("text") if isinstance(result, dict) else None
    if not isinstance(transcript, str) or not transcript.strip():
        raise ValueError("Whisper returned an empty transcript.")
    return transcript.strip()


def load_whisper_model():
    whisper = import_module("whisper")
    return whisper.load_model(WHISPER_MODEL)
