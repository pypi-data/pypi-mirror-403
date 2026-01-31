import numpy as np
from auralis.scorer import score_waveform, score_audio
from auralis.processing import preprocess_audio, AudioTooShortError, get_audio_duration
from auralis.config import SAMPLE_RATE, MIN_DURATION_SEC as TARGET_DURATION
from pathlib import Path
import subprocess
import pytest
import soundfile as sf
import warnings
from unittest.mock import patch

def pytest_configure():
    warnings.filterwarnings(
        "ignore", 
        message = "builtin type SwigPy.* has no __module__ attribute",
        category = DeprecationWarning,
    )

def test_score_waveform():
    fake_audio = np.random.randn(16000).astype("float32")
    score_wav = score_waveform(fake_audio)

    assert isinstance(score_wav, float)

    assert 0.0 <= score_wav <= 100.0

def test_audio_score(tmp_path):
    sr = 16000
    duration_sec = 5

    audio = np.random.randn(sr * duration_sec).astype("float32")

    wav_path = tmp_path / "sample.wav"
    sf.write(wav_path, audio, sr)

    score = score_audio(str(wav_path))

    assert isinstance(score, float)
    assert 0.0 <= score <= 100.0


# def test_score_audio_mocked():
#     with patch("auralis.processing.load_audio") as mock_load:
#         mock_load.return_value = (torch.randn(1, 16000), 16000)

#         score = score_audio("dummy.wav")
#         assert 0.0 <= score <= 100.0
        
def test_preprocess_audio(tmp_path):
    # valid audio
    normal_audio = np.random.randn(int(SAMPLE_RATE * (TARGET_DURATION + 1))).astype("float32")
    normal_file = tmp_path / "normal.wav"
    sf.write(normal_file, normal_audio, SAMPLE_RATE)

    output_dir = tmp_path / "processed"
    output_dir.mkdir()

    processed_files = preprocess_audio(str(tmp_path), str(output_dir))

    assert len(processed_files) == 1

    fpath = Path(processed_files[0])
    assert fpath.exists()
    assert fpath.suffix == ".wav"

    duration = get_audio_duration(str(fpath))
    assert abs(duration - TARGET_DURATION) < 0.1


def test_preprocess_audio_short_file(tmp_path):
    short_audio = np.random.randn(int(SAMPLE_RATE * (TARGET_DURATION - 2))).astype("float32")
    short_file = tmp_path / "short.wav"
    sf.write(short_file, short_audio, SAMPLE_RATE)

    output_dir = tmp_path / "processed"
    output_dir.mkdir()

    with pytest.raises(AudioTooShortError):
        preprocess_audio(str(tmp_path), str(output_dir))
