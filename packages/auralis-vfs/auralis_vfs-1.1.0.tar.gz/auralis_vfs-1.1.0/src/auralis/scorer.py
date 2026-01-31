from .config import LOW_PERCENTILE, HIGH_PERCENTILE, FATIGUE_AXIS, REF_C_H
import numpy as np
from .ecapa import ECAPAENCODER
from .config import CONFIG
from pathlib import Path
from .validators import validate_audio_file
from .processing import load_audio, AudioLoadError

C_h = np.load(REF_C_H)
fatigue_axis = np.load(FATIGUE_AXIS)
low = float(np.load(LOW_PERCENTILE)["arr_0"])
high = float(np.load(HIGH_PERCENTILE)["arr_0"])

_encoder = ECAPAENCODER()

def score_emb(embedding, C_h, fatigue_axis, raw_low, raw_high, method='sigmoid'):
    raw = np.dot(C_h - embedding, fatigue_axis)

    normalized = (raw - raw_low) / (raw_high - raw_low)

    normalized = np.clip(normalized, -0.5, 1.05)

    if method == "linear":
        score = normalized * 100

    elif method == "sigmoid":
        midpoint = 0.5
        scale = 0.25
        score = 1 / (1 + np.exp(-(normalized - midpoint) / scale)) * 100

    elif method == 'smooth_linear':
        scale = 10
        score = normalized * 100
        score = 100 / (1 + np.exp(- (score - 50) / scale))
    else:
        raise ValueError("method must be 'linear', 'sigmoid', or 'smooth_linear'")

    score  = np.clip(score, 0, 100)
    if isinstance(score, np.ndarray):
        score = score.item()
    return float(score)

def score_waveform(waveform: np.ndarray) -> float:
    emb = _encoder.encode(waveform)

    score = score_emb(emb, C_h=C_h, fatigue_axis=fatigue_axis, raw_low=low, raw_high=high)

    return score

def score_audio(path: str | Path) -> float:
    path = Path(path)

    validate_audio_file(path)

    waveform = load_audio(path)
    return score_waveform(waveform)