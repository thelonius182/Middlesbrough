from pathlib import Path
import random

import torch
import torchaudio as ta

from chatterbox.mtl_tts import ChatterboxMultilingualTTS


REFERENCE = "reference.wav"
OUTPUT_DIR = Path("hours_context_test")

CFG_WEIGHT = 0.3

HOURS = {
    10: "tien uur",
    11: "elf uur",
    15: "vijftien uur",
    17: "zeventien uur",
    23: "drieëntwintig uur",
}

SEEDS = {
    10: [25001, 25002, 25003],
    11: [25101, 25102, 25103],
    15: [25501, 25502, 25503],
    17: [25701, 25702, 25703],
    23: [26301, 26302, 26303],
}


def set_seed(seed):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


print("Model laden...")

model = ChatterboxMultilingualTTS.from_pretrained(
    device="cuda",
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True,
)

for hour, text in HOURS.items():
    hour_dir = OUTPUT_DIR / f"{hour:02d}"
    hour_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    for i, seed in enumerate(SEEDS[hour], start=1):
        set_seed(seed)

        output = hour_dir / f"{hour:02d}_{i:02d}.wav"

        print(
            f"{hour:02d} kandidaat {i}: "
            f"seed={seed} -> {output}"
        )

        clip = model.generate(
            f"{text}. vijftien minuten.",
            language_id="nl",
            audio_prompt_path=REFERENCE,
            cfg_weight=CFG_WEIGHT,
        )

        ta.save(
            output,
            clip.cpu(),
            model.sr,
        )

print("Klaar.")
