import soundfile as sf
from .config import MAX_DURATION_SEC, MIN_DURATION_SEC, ALLOWED_EXTENSIONS
from pathlib import Path

class AudioValidationError(ValueError):
    pass


def validate_audio_duration(filepath: str, max_duration: float = MAX_DURATION_SEC):
    try:
        info = sf.info(filepath)
    except RuntimeError:
        raise AudioValidationError("Invalid or corrupted audio file.")

    duration = info.frames / float(info.samplerate)

    if duration > max_duration or duration < MIN_DURATION_SEC:
        raise AudioValidationError(
            f"Audio duration {duration:.2f}s invalid. "
            f"Allowed range: {MIN_DURATION_SEC:.2f}s – {max_duration:.2f}s."
        )

    return duration


def validate_audio_file(file_path: str):
    path = Path(file_path)

    if not path.exists():
        raise AudioValidationError(f"Audio file does not exist: {file_path}")

    ext = path.suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise AudioValidationError(
            f"Unsupported file type {ext}. Allowed formats are: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    validate_audio_duration(str(path))