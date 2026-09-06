from pathlib import Path

import torch
import torchaudio as ta


SOURCE = Path("hour_01_context_test/01_02.wav")
TARGET = Path("hour_01_context_test/01_extracted.wav")

END_SECONDS = 0.64


wav, sr = ta.load(SOURCE)

end_sample = int(END_SECONDS * sr)
fragment = wav[:, :end_sample].clone()

fade = min(
    int(sr * 0.010),
    fragment.shape[-1],
)

if fade > 0:
    fragment[:, -fade:] *= torch.linspace(
        1.0,
        0.0,
        fade,
    )

ta.save(
    TARGET,
    fragment,
    sr,
)

print(f"Gemaakt: {TARGET}")
print(f"Duur: {fragment.shape[-1] / sr:.3f} s")
