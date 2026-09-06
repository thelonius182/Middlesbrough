from pathlib import Path
import shutil

import torchaudio as ta


HOURS = [10, 11, 15, 17, 23]

SOURCE_ROOT = Path("hours_context_test/extracted")
TARGET_ROOT = Path("samples/hours")
BACKUP_ROOT = Path("sample_backups/hours")


BACKUP_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)

for hour in HOURS:
    source = SOURCE_ROOT / f"{hour:02d}_extracted.wav"
    target = TARGET_ROOT / f"{hour:02d}.wav"
    backup = BACKUP_ROOT / f"{hour:02d}_before_regen.wav"

    if not source.exists():
        raise FileNotFoundError(
            f"Bron ontbreekt: {source}"
        )

    if target.exists() and not backup.exists():
        shutil.copy2(
            target,
            backup,
        )

    wav, sr = ta.load(source)

    ta.save(
        target,
        wav,
        sr,
        encoding="PCM_S",
        bits_per_sample=16,
    )

    print(
        f"{hour:02d}: {target} "
        f"({wav.shape[-1] / sr:.3f} s)"
    )

print()
print("Klaar.")
