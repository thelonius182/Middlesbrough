from pathlib import Path
import shutil

import torch
import torchaudio as ta


SOURCE = Path("hour_02_context_test/02_02.wav")
TARGET = Path("samples/hours/02.wav")
BACKUP = Path("samples/hours/02_old.wav")

# Gemeten pauze begint rond 0.68 s.
# We bewaren circa 20 ms van die pauze.
END_SECONDS = 0.70


wav, sr = ta.load(SOURCE)

end_sample = int(END_SECONDS * sr)
fragment = wav[:, :end_sample].clone()

# Alleen een korte fade in het stille stukje aan het einde.
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

if TARGET.exists() and not BACKUP.exists():
    shutil.copy2(TARGET, BACKUP)

ta.save(
    TARGET,
    fragment,
    sr,
)

print(f"Gemaakt: {TARGET}")
print(f"Duur: {fragment.shape[-1] / sr:.3f} s")
print(f"Backup: {BACKUP}")
