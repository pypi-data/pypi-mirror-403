import numpy as np
import torch
import os
import subprocess
import torchaudio
from .config import SAMPLE_RATE, DEVICE, N_MELS, TARGET_LEN, SUPPORTED_FORMATS, MIN_DURATION_SEC as TARGET_DURATION
from pydub import AudioSegment
import torch.nn.functional as F

mel_transform = torchaudio.transforms.MelSpectrogram(
    sample_rate = SAMPLE_RATE,
    n_mels = N_MELS,
    n_fft = 400,
    hop_length = 256,
    
).to(DEVICE)

amp_to_db = torchaudio.transforms.AmplitudeToDB().to(DEVICE)

class AudioTooShortError(Exception):
    pass
class AudioLoadError(Exception):
    pass

def load_audio(path: str) -> torch.Tensor:
    waveform = None
    sr = None

    try:
        waveform, sr = torchaudio.load(path)
    except Exception as e1:
        try:
            audio = AudioSegment.from_file(path)
            audio = audio.set_channels(1).set_frame_rate(SAMPLE_RATE)
            samples = np.array(audio.get_array_of_samples(), dtype=np.float32)

            if samples.size == 0:
                raise AudioLoadError("Empty audio file")

            waveform = torch.from_numpy(samples)
            sr = SAMPLE_RATE
        except Exception as e2:
            raise AudioLoadError(f"Failed to decode audio file: {str(e2)}") from e2

    if waveform is None or waveform.numel() == 0:
        raise AudioLoadError("Failed to load audio or audio is empty")

    if waveform.dim() > 1:
        waveform = waveform.mean(dim = 0)

    if sr!=SAMPLE_RATE:
        waveform = torchaudio.transforms.Resample(sr, SAMPLE_RATE)(waveform)

    if waveform.numel() < TARGET_LEN:
        raise AudioLoadError("Audio too short for analysis")

    if waveform.numel() > TARGET_LEN:
        waveform = waveform[:TARGET_LEN]
    else:
        waveform = F.pad(waveform, (0, TARGET_LEN - waveform.numel()))

    return waveform.float()

def waveform_to_mel(waveform: torch.Tensor):
    mel = mel_transform(waveform.unsqueeze(0))
    mel = amp_to_db(mel)
    mel = mel.transpose(1, 2)
    return mel

def pad_time_dim(mel):
    T = mel.shape[1]
    pad_len = (8 - (T % 8)) % 8
    if pad_len > 0:
        mel = F.pad(mel, (0,0,0,pad_len))
    return mel

def extract_features(wav: torch.Tensor) -> torch.Tensor:
    mel = mel_transform(wav.unsqueeze(0))
    mel = amp_to_db(mel)
    if mel.dim == 4:
        mel = mel.squeeze(1)

    mel.transpose(1, 2)  # [B, T, N_MELS]
    mel = pad_time_dim(mel)
    return mel

def get_audio_duration(file_path: str) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        file_path
    ]
    
    result = subprocess.run(
        cmd, stdout = subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed to get audio duration of {file_path}: {result.stderr}")
    
    return float(result.stdout.strip())

def preprocess_audio(input_path: str, output_dir: str = None):
    if os.path.isfile(input_path):
        files = [input_path]
        base_dir = os.path.dirname(input_path)
    elif os.path.isdir(input_path):
        files = [
            os.path.join(input_path, f)
            for f in os.listdir(input_path)
            if f.lower().endswith(SUPPORTED_FORMATS)
        ]
        base_dir = input_path
    else:
        raise ValueError(f"Invalid input path: {input_path}")

    if output_dir is None:
        output_dir = base_dir
    else:
        os.makedirs(output_dir, exist_ok=True)

    processed_files = []
    short_files = []

    for input_file in files:
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_path = os.path.join(output_dir, f"{base_name}_preprocessed.wav")

        duration = get_audio_duration(input_file)

        if duration < TARGET_DURATION:
            short_files.append(input_file)
            continue

        cmd = [
            "ffmpeg", "-y",
            "-i", input_file,
            "-ac", "1",
            "-ar", str(SAMPLE_RATE),
            "-t", str(TARGET_DURATION),
            output_path
        ]

        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed for {input_file}: {result.stderr}")

        processed_files.append(output_path)

    if len(processed_files) == 0 and len(short_files) > 0:
        raise AudioTooShortError(f"All audio files are shorter than {TARGET_DURATION}s")

    if len(processed_files) == 0:
        raise RuntimeError("No valid audio files found for preprocessing.")

    return processed_files