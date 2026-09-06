from pathlib import Path

import torch
import torchaudio as ta


FILES = [
    Path("minute_context_test/05_02.wav"),
    Path("minute_context_test/17_02.wav"),
    Path("minute_context_test/43_02.wav"),
]

FRAME_MS = 20
HOP_MS = 10


for path in FILES:
    wav, sr = ta.load(path)
    x = wav.mean(dim=0)

    frame = int(sr * FRAME_MS / 1000)
    hop = int(sr * HOP_MS / 1000)

    envelope = (
        x.abs()
        .unfold(0, frame, hop)
        .mean(dim=1)
    )

    print()
    print("=" * 60)
    print(path)
    print(f"duur: {x.numel() / sr:.2f} s")
    print(f"minimum energie: {envelope.min().item():.6f}")
    print(f"maximum energie: {envelope.max().item():.6f}")

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
            start_s = begin * HOP_MS / 1000
            end_s = end * HOP_MS / 1000
            duration_ms = (end - begin) * HOP_MS

            # Begin- en eindstilte niet tonen.
            if start_s > 0.2 and end_s < x.numel() / sr - 0.2:
                if duration_ms >= 30:
                    internal.append(
                        (round(start_s, 2), round(end_s, 2), duration_ms)
                    )

        print(
            f"drempel {threshold:.3f}: {internal}"
        )
