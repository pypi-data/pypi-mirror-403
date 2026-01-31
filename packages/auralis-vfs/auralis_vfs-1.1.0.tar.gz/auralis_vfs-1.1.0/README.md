# Auralis VFS (Vocal Fatigue Scoring Library)

[![PyPI](https://img.shields.io/pypi/v/auralis-vfs?style=flat-square)](https://pypi.org/project/auralis-vfs/)
[![Python](https://img.shields.io/pypi/pyversions/auralis-vfs?style=flat-square)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Overview

***auralis_vfs*** is a research-oriented Python library for objective vocal fatigue scoring from speech signals. It provides an end-to-end pipeline for standardized audio preprocessing and embedding-based inference using the proposed ECAPA-TDNN-VHE model, a contrastively trained neural speech encoder designed to quantify deviations in vocal health.

The library is designed to support both experimental research workflows and practical system integration, enabling reproducible vocal fatigue analysis from raw waveform input or audio files with minimal configuration.

***auralis_vfs*** exposes high-level APIs for:

- Direct scoring from raw waveforms (score_waveform)
- Scoring from audio files (score_audio)
- Deterministic and batch-capable audio preprocessing (preprocess_audio)

The preprocessing module enforces a strict and reproducible audio standardization protocol, ensuring compatibility with the ECAPA-TDNN-VHE inference pipeline.

This library is designed for:

* Research studies in voice health, occupational voice monitoring, and speech pathology.
* Integration into speech analysis pipelines.
* Reproducible and standardized scoring across datasets.

---

## Key Features

* Compute **Vocal Fatigue Score** from raw audio (`.wav`, `.mp3`, `.m4a`).
* Fast waveform-based scoring using health centric vocal health encoder **ECAPA-TDNN-VHE embeddings**.
* Reference-based scoring using curated embeddings from healthy speakers.
* **Production-ready API** with `score_audio()` and `score_waveform()` functions.
* `preprocess_audio` function for making the audio compatible for passing into `score_audio` function.
* Configurable parameters for audio sampling rate, duration, and mel-spectrogram features.
* Designed for **research reproducibility**.

---

## Research Orientation

***auralis_vfs*** is built upon the ECAPA-TDNN-VHE model, which is trained using supervised contrastive learning to emphasize vocal health states while suppressing speaker identity information. The library is intended for:

- Vocal health research
- Speech pathology experiments
- Longitudinal voice monitoring
- Clinical decision-support prototyping
- Embedded AI health systems

The implementation prioritizes:

- Reproducibility
- Deterministic preprocessing
- Model-driven scoring rather than heuristic acoustic metrics
- Compatibility with downstream MLOps and API services

### Benchmarking Against Baseline ECAPA-TDNN

The model was evaluated on vocal health classification tasks. Results highlight **ECAPA-TDNN-VHE's superiority over baseline ECAPA-TDNN**:

| Model | Accuracy | Macro F1 | Healthy F1 | Strained F1 | Stressed F1 |
|------|----------|----------|------------|-------------|-------------|
| ECAPA-TDNN (SpeechBrain baseline) | 0.36 | 0.31 | 0.50 | 0.22 | 0.22 |
| **ECAPA-TDNN-VHE (Khubaib et al., 2026)** | **0.78** | **0.77** | **0.85** | **0.78** | **0.70** |

This demonstrates **state-of-the-art health-centric embedding performance** within ECAPA-based architectures.

**Cite our research:**

> Ahmad, M. K. (2026). Modeling Vocal Fatigue as Embedding-Space Deviation Using Contrastively Trained ECAPA-TDNNs (0.1.0). Zenodo. https://doi.org/10.5281/zenodo.18305757


## Installation

```bash
pip install auralis-vfs
```

**Dependencies:**

* Python >= 3.10
* torch >= 2.1.1
* torchaudio >= 2.1.1
* speechbrain >= 1.0.3
* numpy >= 1.23
* soundfile
* scipy
* pydub
* PyYAML

> Optional: GPU acceleration works automatically if PyTorch detects a CUDA-enabled device.

---

## Usage

### 1. Scoring a waveform

```python
import numpy as np
from auralis.scorer import score_waveform

# Generate fake waveform (1 second of audio at 16kHz)
waveform = np.random.randn(16000).astype("float32")

score = score_waveform(waveform)
print(f"Vocal Fatigue Score: {score:.2f}")
```

### 2. Scoring an audio file

```python
from auralis.scorer import score_audio

audio_path = "path/to/speech_sample.wav"
score = score_audio(audio_path)
print(f"Vocal Fatigue Score: {score:.2f}")
```

### 3. Audio Preprocessing

The preprocess_audio function standardizes raw audio into a format compatible with the vocal fatigue scoring pipeline.
It converts audio to:

- WAV format
- Mono channel
- 16 kHz sampling rate
- Fixed duration of 5 seconds

> Audio shorter than the required minimum(5 seconds) duration is rejected with a validation error.

##### Requirements

> Ensure ffmpeg is installed and available in your system PATH.

```python
ffmpeg -version
```

#### Basic Usage (Single Audio File)
```python
from auralis.processing import preprocess_audio

input_audio = "data/sample.ogg"

processed_files = preprocess_audio(input_audio)

print(processed_files)
# ['data/sample_preprocessed.wav']
```

#### Batch Processing (Directory of Audio Files)
```python
from auralis.processing import preprocess_audio

input_dir = "data/raw_audio"
output_dir = "data/processed_audio"

processed_files = preprocess_audio(input_dir, output_dir)

for path in processed_files:
    print(path)
```

All supported audio files in the directory are processed and saved to the output directory.

#### Supported Audio Formats

The function processes files with the following extensions:

```python
.wav, .mp3, .ogg, .flac, .m4a, .aac
```


>## Audio Validation

- Supported formats for direct passing to `score_audio` function: .wav, .mp3, .m4a
- Duration: 5–10 seconds recommended

> Scores range from **0 (no fatigue)** to **100 (severe fatigue)**.

---

## File & Directory Structure

```
auralis-vfs/
├─ src/auralis/
│  ├─ __init__.py
│  ├─ scorer.py          # Public API functions
|  ├─ validators.py
│  ├─ ecapa.py           # Model wrapper
│  ├─ processing.py      # Audio & feature processing
│  ├─ config.py          # Paths & constants
│  ├─ data/              # Reference embeddings & axis
│  └─ models/            # Pretrained ECAPA-TDNN-VHE model & config.yaml
├─ tests/
│  ├─ test_scoring.py
├─ pyproject.toml
├─ setup.cfg
├─ CITATIONS.cff
├─ MANIFEST.in
├─ .gitignore
├─ README.md
├─ requirements.txt
└─ LICENSE
```

---

## API Reference

### `score_waveform(waveform: np.ndarray) -> float`

* `waveform`: 1D numpy array representing audio samples.
* Returns: Vocal Fatigue Score (float, 0–100).

### `score_audio(file_path: str) -> float`

* `file_path`: Path to audio file (`.wav`, `.mp3`, `.m4a`).
* Validates file extension and duration.
* Returns: Vocal Fatigue Score (float, 0–100).

### `preprocess_audio(input_path/dir: str, output_dir: str)`

* `input_path` to audio file to be preprocessed.
* Preprocesses the audio file and saves in the same dir if output_dir is not provided.
* Prints the path where the preprocessed file/files are stored.
---

## Future Work

Planned improvements to enhance auralis_vfs:

- **Prosody Feature Integration** – Analyze pitch, energy, and speaking rate to enrich scoring.

- **Clinical Report Generation** – Provide automatic reports resembling clinical assessments, including:

    - Fatigue trends over time
    - Prosody-based analysis
    - Summary interpretation for voice health monitoring


- **Web/API Interface** – Seamless integration with Gradio or FastAPI for cloud deployments.

## Contributors & Credits

**Authors / Maintainers:**

* **Muhammad Khubaib Ahmad** – AI/ML Architect, Vocal Fatigue Modeling

**Contributors:**

* **Faiez Ahmad(Data Manager)** – Dataset collection and preprocessing
* **Muhammad Anas Tariq(Data Collector)** – Dataset organization and verification

---

## License

This project is licensed under the **MIT License** – see the [LICENSE](LISENCE) file for details.

---

## Notes for Researchers

* Designed for **short audio clips** (5–10 seconds).
* Scores are **relative to healthy reference embeddings**.
* Reproducibility is guaranteed by **fixed model weights and configuration files**.
* Compatible with both **CPU and GPU** setups.

---

## Contact

* **Email**: [muhammadkhubaibahmad854@gmail.com](mailto:muhammadkhubaibahmad854@gmail.com)
* **GitHub**: [Khubaib8281/auralis-vfs](https://github.com/Khubaib8281/auralis-vfs)