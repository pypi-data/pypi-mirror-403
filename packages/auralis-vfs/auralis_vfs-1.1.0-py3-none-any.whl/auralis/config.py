from pathlib import Path
import torch
import yaml

# __file__ is src/auralis/config.py, so parent.parent goes to src/
BASE_DIR = Path(__file__).resolve().parent  # src/auralis

MODEL_DIR = BASE_DIR / "models" / "ecapa_supcon_model.pth"
REF_EMB = BASE_DIR / "data" / "reference_embeddings_192-d.npy"
REF_C_H = BASE_DIR / "data" / "centroid_healthy.npy"
FATIGUE_AXIS = BASE_DIR / "data" / "fatigue_axis.npy"
LOW_PERCENTILE = BASE_DIR / "data" / "low_percentile.npz"  
HIGH_PERCENTILE = BASE_DIR / "data" / "high_percentile.npz"
CONFIG_PATH = BASE_DIR / "models" / "config.yaml"

SAMPLE_RATE = 16000
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
TARGET_SEC = 5
N_MELS = 80
TARGET_LEN = SAMPLE_RATE * TARGET_SEC
MAX_DURATION_SEC = 10.0
MIN_DURATION_SEC = 5.0
ALLOWED_EXTENSIONS = {".wav", ".mp3", ".m4a"}
SUPPORTED_FORMATS = (".wav", ".mp3", ".m4a", ".ogg", ".flac", ".aac")

# Load YAML
with open(CONFIG_PATH, "r") as f:
    CONFIG = yaml.safe_load(f)


# print(f"Model directory is set to: {MODEL_DIR}")
# print(f"base dir: {BASE_DIR}")
# print(f"ref emb path: {REF_EMB}")