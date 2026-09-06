from pathlib import Path
import random
import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS


REFERENCE = "reference.wav"
OUTPUT_DIR = Path("sample_candidates")

CFG_WEIGHT = 0.3
CANDIDATES = 3
BASE_SEED = 2000


def trim_fragment(clip, sr):
    x = clip.squeeze(0)

    frame = int(sr * 0.020)
    hop = int(sr * 0.010)

    if x.numel() < frame:
        return clip.cpu()

    envelope = (
        x.abs()
        .unfold(0, frame, hop)
        .mean(dim=1)
    )

    threshold = max(
        0.004,
        envelope.max().item() * 0.05,
    )

    actief = (envelope > threshold).nonzero()

    if len(actief) == 0:
        return clip.cpu()

    laatste_frame = actief[-1].item()
    einde = laatste_frame * hop + frame

    einde = min(
        einde + int(sr * 0.030),
        x.numel(),
    )

    x = x[:einde].clone()

    fade = min(
        int(sr * 0.025),
        x.numel(),
    )

    if fade > 0:
        x[-fade:] *= torch.linspace(
            1.0,
            0.0,
            fade,
            device=x.device,
        )

    return x.unsqueeze(0).cpu()


def set_seed(seed):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


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


SAMPLES = [
    ("intro", "intro", "Bij de volgende toon is het"),
    ("exact", "precies", "precies"),
]

for uur in range(24):
    SAMPLES.append(
        ("hours", f"{uur:02d}", f"{getal(uur)} uur")
    )

for minuut in range(1, 60):
    woord = "minuut" if minuut == 1 else "minuten"

    SAMPLES.append(
        (
            "minutes",
            f"{minuut:02d}",
            f"{getal(minuut)} {woord}",
        )
    )

for seconde in (10, 20, 30, 40, 50):
    SAMPLES.append(
        (
            "seconds",
            f"{seconde:02d}",
            f"en {getal(seconde)} seconden",
        )
    )

print("Model laden...")

model = ChatterboxMultilingualTTS.from_pretrained(
    device="cuda",
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for sample_index, (groep, naam, tekst) in enumerate(SAMPLES):
    directory = OUTPUT_DIR / groep
    directory.mkdir(parents=True, exist_ok=True)

    print()
    print(f"{groep}/{naam}: {tekst}")

    for candidate in range(1, CANDIDATES + 1):
        seed = BASE_SEED + sample_index * 100 + candidate

        set_seed(seed)

        output = directory / f"{naam}_{candidate:02d}.wav"

        print(
            f"  kandidaat {candidate}: "
            f"seed={seed} -> {output}"
        )

        clip = model.generate(
            tekst,
            language_id="nl",
            audio_prompt_path=REFERENCE,
            cfg_weight=CFG_WEIGHT,
        )

        clip = trim_fragment(
            clip,
            model.sr,
        )

        ta.save(
            output,
            clip,
            model.sr,
        )

print()
print("Klaar.")
