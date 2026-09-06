from pathlib import Path

import torch
import torchaudio as ta


INPUT_DIR = Path("minute_context_test")
OUTPUT_DIR = Path("minute_extracted_test")

FILES = [
    "05_02.wav",
    "17_02.wav",
    "43_02.wav",
]

FRAME_MS = 20
HOP_MS = 10

THRESHOLD = 0.020
MIN_SILENCE_MS = 50
EDGE_SILENCE_MS = 20


def find_silences(x, sr):
    frame = int(sr * FRAME_MS / 1000)
    hop = int(sr * HOP_MS / 1000)

    envelope = (
        x.abs()
        .unfold(0, frame, hop)
        .mean(dim=1)
    )

    silent = envelope < THRESHOLD

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

    result = []

    for begin, end in runs:
        duration_ms = (end - begin) * HOP_MS

        if duration_ms < MIN_SILENCE_MS:
            continue

        start_s = begin * hop / sr
        end_s = end * hop / sr

        result.append(
            (start_s, end_s, duration_ms)
        )

    return result


def extract_minute(wav, sr):
    x = wav.mean(dim=0)
    duration = x.numel() / sr

    silences = find_silences(x, sr)

    # Eerste zinsgrens:
    # na "Bij de volgende toon is het drie uur."
    first_candidates = [
        s for s in silences
        if duration * 0.40 <= s[0] <= duration * 0.60
    ]

    # Tweede zinsgrens:
    # vóór "precies."
    second_candidates = [
        s for s in silences
        if duration * 0.68 <= s[0] <= duration * 0.88
    ]

    if not first_candidates:
        raise RuntimeError(
            f"Eerste zinsgrens niet gevonden. Stiltes: {silences}"
        )

    if not second_candidates:
        raise RuntimeError(
            f"Tweede zinsgrens niet gevonden. Stiltes: {silences}"
        )

    # Kies in elk venster de langste stilte.
    first = max(
        first_candidates,
        key=lambda s: s[2],
    )

    second = max(
        second_candidates,
        key=lambda s: s[2],
    )

    print(
        f"  grenzen: "
        f"{first[0]:.2f}-{first[1]:.2f} / "
        f"{second[0]:.2f}-{second[1]:.2f}"
    )

    # Laat aan beide kanten een klein stukje van de
    # gevonden stilte staan.
    start_s = max(
        first[0],
        first[1] - EDGE_SILENCE_MS / 1000,
    )

    end_s = min(
        second[1],
        second[0] + EDGE_SILENCE_MS / 1000,
    )

    start_sample = int(start_s * sr)
    end_sample = int(end_s * sr)

    fragment = wav[:, start_sample:end_sample].clone()

    # Zeer korte fades tegen klikjes.
    fade = min(
        int(sr * 0.010),
        fragment.shape[-1],
    )

    if fade > 0:
        fragment[:, :fade] *= torch.linspace(
            0.0,
            1.0,
            fade,
        )

        fragment[:, -fade:] *= torch.linspace(
            1.0,
            0.0,
            fade,
        )

    return fragment


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

for filename in FILES:
    source = INPUT_DIR / filename

    wav, sr = ta.load(source)

    print()
    print(source)

    fragment = extract_minute(
        wav,
        sr,
    )

    target = OUTPUT_DIR / filename

    ta.save(
        target,
        fragment,
        sr,
    )

    print(
        f"  -> {target} "
        f"({fragment.shape[-1] / sr:.2f} s)"
    )

print()
print("Klaar.")
