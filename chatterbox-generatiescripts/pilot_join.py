from pathlib import Path

import torch
import torchaudio as ta


BASE = Path("sample_candidates")
OUTPUT = "pilot_join.wav"

PAUZE = 0.45

FILES = [
    BASE / "intro" / "intro_03.wav",
    BASE / "hours" / "03_02.wav",
    BASE / "minutes" / "01_02.wav",
    BASE / "seconds" / "30_02.wav",
]


clips = []
sample_rate = None

for path in FILES:
    wav, sr = ta.load(path)

    if sample_rate is None:
        sample_rate = sr
    elif sr != sample_rate:
        raise ValueError(
            f"Sample rate van {path} is {sr}, verwacht {sample_rate}"
        )

    clips.append(wav)

stilte = torch.zeros(
    1,
    int(sample_rate * PAUZE),
)

onderdelen = []

for i, clip in enumerate(clips):
    if i > 0:
        onderdelen.append(stilte)

    onderdelen.append(clip)

wav = torch.cat(onderdelen, dim=-1)

ta.save(
    OUTPUT,
    wav,
    sample_rate,
)

print(f"Gemaakt: {OUTPUT}")
