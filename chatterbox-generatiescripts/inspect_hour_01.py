from pathlib import Path

import torchaudio as ta


PATH = Path("hour_01_context_test/01_02.wav")

FRAME_MS = 20
HOP_MS = 10


wav, sr = ta.load(PATH)
x = wav.mean(dim=0)

frame = int(sr * FRAME_MS / 1000)
hop = int(sr * HOP_MS / 1000)

envelope = (
    x.abs()
    .unfold(0, frame, hop)
    .mean(dim=1)
)

print(f"duur: {x.numel() / sr:.2f} s")

for threshold in (0.003, 0.005, 0.008, 0.012, 0.020):
    silent = envelope < threshold

    runs = []
    start = None

    for i, value in enumerate(silent.tolist()):
        if value:
            if start is None:
                start = i
        elif start is not None:
            runs.append((start, i))
            start = None

    if start is not None:
        runs.append((start, len(silent)))

    internal = []

    for begin, end in runs:
        duration_ms = (end - begin) * HOP_MS

        if duration_ms >= 30:
            internal.append(
                (
                    round(begin * HOP_MS / 1000, 2),
                    round(end * HOP_MS / 1000, 2),
                    duration_ms,
                )
            )

    print(
        f"drempel {threshold:.3f}: {internal}"
    )
