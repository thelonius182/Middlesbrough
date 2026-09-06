from pathlib import Path
import random

import torch
import torchaudio as ta

from chatterbox.mtl_tts import ChatterboxMultilingualTTS


REFERENCE = "reference.wav"
OUTPUT_DIR = Path("hour_01_context_test")

CFG_WEIGHT = 0.3
SEEDS = [24001, 24002, 24003]


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

    output = OUTPUT_DIR / f"01_{i:02d}.wav"

    print(f"kandidaat {i}: seed={seed}")

    clip = model.generate(
        "één uur. vijftien minuten.",
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
