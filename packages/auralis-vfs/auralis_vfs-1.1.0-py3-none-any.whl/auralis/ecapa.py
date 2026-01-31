import torch
import torchaudio
from speechbrain.lobes.models.ECAPA_TDNN import ECAPA_TDNN
import numpy as np
from .config import MODEL_DIR, DEVICE, N_MELS
from .processing import waveform_to_mel

class ECAPAENCODER:
    def __init__(self):
        self.ecapa = ECAPA_TDNN(
            input_size = N_MELS,
            lin_neurons = 192,
            channels = [512, 512, 512],
            dilations = [1, 2, 3],
            kernel_sizes=[5, 3, 3]
        ).to(DEVICE)

        checkpoint = torch.load(MODEL_DIR, map_location=DEVICE)
        self.ecapa.load_state_dict(checkpoint["ecapa_state_dict"])
        self.ecapa.eval()

    @torch.no_grad()
    def encode(self, waveform):
        if isinstance(waveform, np.ndarray):
            waveform = torch.from_numpy(waveform)
            
        if waveform.ndim == 2 and waveform.shape[0] == 1:
            waveform = waveform.squeeze(0)
        if waveform.ndim != 1:
            raise ValueError(f"Expected waveform [T], got {waveform.shape}")

        waveform = waveform.float().to(DEVICE)
        mel = waveform_to_mel(waveform)

        # print("ECAPA input shape: ", mel.shape)
        emb = self.ecapa(mel)
        return emb.squeeze(0).cpu().numpy()