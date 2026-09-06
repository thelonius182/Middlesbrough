from pathlib import Path
import random

import torch
import torchaudio as ta

from chatterbox.mtl_tts import ChatterboxMultilingualTTS


REFERENCE = "reference.wav"
OUTPUT_DIR = Path("minute_context_test")

CFG_WEIGHT = 0.3
CANDIDATES = 3
BASE_SEED = 5000


def set_seed(seed):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


TESTS = {
    "05": "Bij de volgende toon is het drie uur. vijf minuten. precies.",
    "17": "Bij de volgende toon is het drie uur. zeventien minuten. precies.",
    "43": "Bij de volgende toon is het drie uur. drieënveertig minuten. precies.",
}


print("Model laden...")

model = ChatterboxMultilingualTTS.from_pretrained(
    device="cuda",
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

for name, text in TESTS.items():
    print()
    print(f"{name}: {text}")

    for candidate in range(1, CANDIDATES + 1):
        seed = BASE_SEED + int(name) * 10 + candidate
        set_seed(seed)

        output = OUTPUT_DIR / f"{name}_{candidate:02d}.wav"

        print(
            f"  kandidaat {candidate}: "
            f"seed={seed} -> {output}"
        )

        clip = model.generate(
            text,
            language_id="nl",
            audio_prompt_path=REFERENCE,
            cfg_weight=CFG_WEIGHT,
        )

        ta.save(
            output,
            clip.cpu(),
            model.sr,
        )

print()
print("Klaar.")
