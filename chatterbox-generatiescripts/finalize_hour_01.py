from pathlib import Path
import shutil

import torchaudio as ta


SOURCE = Path("hour_01_context_test/01_extracted.wav")
TARGET = Path("samples/hours/01.wav")
BACKUP = Path("sample_backups/hours/01_before_regen.wav")


BACKUP.parent.mkdir(
    parents=True,
    exist_ok=True,
)

if TARGET.exists() and not BACKUP.exists():
    shutil.copy2(
        TARGET,
        BACKUP,
    )

wav, sr = ta.load(SOURCE)

ta.save(
    TARGET,
    wav,
    sr,
    encoding="PCM_S",
    bits_per_sample=16,
)

print(f"Gemaakt: {TARGET}")
print(f"Duur: {wav.shape[-1] / sr:.3f} s")
print(f"Backup: {BACKUP}")
