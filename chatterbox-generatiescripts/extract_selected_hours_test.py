from pathlib import Path

import torch
import torchaudio as ta


CUTS = {
    10: 0.70,
    11: 0.86,
    15: 0.85,
    17: 1.02,
    23: 1.02,
}

SOURCE_ROOT = Path("hours_context_test")
TARGET_ROOT = Path("hours_context_test/extracted")


TARGET_ROOT.mkdir(
    parents=True,
    exist_ok=True,
)

for hour, end_seconds in CUTS.items():
    source = (
        SOURCE_ROOT
        / f"{hour:02d}"
        / f"{hour:02d}_01.wav"
    )
    target = (
        TARGET_ROOT
        / f"{hour:02d}_extracted.wav"
    )

    wav, sr = ta.load(source)

    end_sample = int(end_seconds * sr)
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
        target,
        fragment,
        sr,
    )

    print(
        f"{hour:02d}: "
        f"{end_seconds:.2f} s -> {target}"
    )
