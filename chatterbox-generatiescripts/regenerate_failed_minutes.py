from pathlib import Path
import random

import torch
import torchaudio as ta

from chatterbox.mtl_tts import ChatterboxMultilingualTTS


REFERENCE = "reference.wav"

CONTEXT_DIR = Path("minute_context_candidates")
OUTPUT_DIR = Path("minute_candidates")

CFG_WEIGHT = 0.3
CANDIDATES = 3
BASE_SEED = 6000

FRAME_MS = 20
HOP_MS = 10
THRESHOLD = 0.020
MIN_SILENCE_MS = 50
EDGE_SILENCE_MS = 20


def getal(n):
    klein = [
        "nul", "één", "twee", "drie", "vier",
        "vijf", "zes", "zeven", "acht", "negen",
        "tien", "elf", "twaalf", "dertien", "veertien",
        "vijftien", "zestien", "zeventien", "achttien", "negentien",
    ]

    if n < 20:
        return klein[n]

    tientallen = {
        20: "twintig",
        30: "dertig",
        40: "veertig",
        50: "vijftig",
    }

    if n in tientallen:
        return tientallen[n]

    eenheden = {
        1: "eenen",
        2: "tweeën",
        3: "drieën",
        4: "vieren",
        5: "vijfen",
        6: "zesen",
        7: "zevenen",
        8: "achten",
        9: "negenen",
    }

    tiental = (n // 10) * 10
    eenheid = n % 10

    return eenheden[eenheid] + tientallen[tiental]


def set_seed(seed):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


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

        result.append(
            (
                begin * hop / sr,
                end * hop / sr,
                duration_ms,
            )
        )

    return result


def extract_minute(wav, sr):
    x = wav.mean(dim=0)
    duration = x.numel() / sr

    silences = find_silences(x, sr)

    # De eerste contextzin is steeds even lang.
    first_candidates = [
        s for s in silences
        if 1.40 <= s[0] <= 2.15
    ]

    # "precies" staat aan het einde; zoek de voorafgaande pauze.
    second_candidates = [
        s for s in silences
        if duration - 1.35 <= s[0] <= duration - 0.35
    ]

    if not first_candidates:
        raise RuntimeError(
            f"Eerste grens niet gevonden: {silences}"
        )

    if not second_candidates:
        raise RuntimeError(
            f"Tweede grens niet gevonden: {silences}"
        )

    first = max(
        first_candidates,
        key=lambda s: s[2],
    )

    second_candidates = [
        s for s in second_candidates
        if s[0] > first[1] + 0.25
    ]

    if not second_candidates:
        raise RuntimeError(
            f"Tweede grens ligt niet na eerste grens: {silences}"
        )

    second = max(
        second_candidates,
        key=lambda s: s[2],
    )

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


print("Model laden...")

model = ChatterboxMultilingualTTS.from_pretrained(
    device="cuda",
)

CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

failed = []

TO_REGENERATE = [
    (0, 1),
    (0, 2),
    (0, 3),
]

for minute, candidate in TO_REGENERATE:
    woord = "minuut" if minute == 1 else "minuten"
    minuuttekst = f"{getal(minute)} {woord}"

    contexttekst = (
        f"Bij de volgende toon is het drie uur. "
        f"{minuuttekst}. precies."
    )

    # Nieuwe seed, zodat we echt een andere generatie krijgen.
    seed = 16000 + minute * 10 + candidate
    set_seed(seed)

    context_path = (
        CONTEXT_DIR /
        f"{minute:02d}_{candidate:02d}.wav"
    )

    output_path = (
        OUTPUT_DIR /
        f"{minute:02d}_{candidate:02d}.wav"
    )

    print()
    print(
        f"{minute:02d}_{candidate:02d}: "
        f"{minuuttekst}, seed={seed}"
    )

    clip = model.generate(
        contexttekst,
        language_id="nl",
        audio_prompt_path=REFERENCE,
        cfg_weight=CFG_WEIGHT,
    )

    clip = clip.cpu()

    ta.save(
        context_path,
        clip,
        model.sr,
    )

    try:
        fragment = extract_minute(
            clip,
            model.sr,
        )

        ta.save(
            output_path,
            fragment,
            model.sr,
        )

        print("  geknipt")

    except RuntimeError as error:
        print(f"  KNIPPEN MISLUKT: {error}")

        failed.append(
            (
                minute,
                candidate,
                str(error),
            )
        )

print()
print("Klaar.")

if failed:
    print()
    print("Nog steeds niet automatisch geknipt:")

    for minute, candidate, error in failed:
        print(
            f"  {minute:02d}_{candidate:02d}: {error}"
        )
else:
    print("Alle drie opnieuw gegenereerd en geknipt.")

