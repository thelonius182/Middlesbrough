from pathlib import Path
import random

import torch
import torchaudio as ta

from chatterbox.mtl_tts import ChatterboxMultilingualTTS


REFERENCE = "reference.wav"
OUTPUT_DIR = Path("hour_02_candidates")

CFG_WEIGHT = 0.3

SEEDS = [
    22001,
    22002,
    22003,
]


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

for i, seed in enumerate(SEEDS, start=1):
    set_seed(seed)

    output = OUTPUT_DIR / f"02_{i:02d}.wav"

    print(
        f"kandidaat {i}: seed={seed} -> {output}"
    )

    clip = model.generate(
        "twee uur",
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
