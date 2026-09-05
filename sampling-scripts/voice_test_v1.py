import torchaudio as ta
import torch

from chatterbox.mtl_tts import ChatterboxMultilingualTTS


REFERENCE = "reference.wav"
OUTPUT = "klok_test.wav"

TEXT = (
    "Bij de volgende toon is het zestien uur, "
    "twaalf minuten, "
    "en twintig seconden."
)

model = ChatterboxMultilingualTTS.from_pretrained(
    device="cuda",
)

wav = model.generate(
    TEXT,
    language_id="nl",
    audio_prompt_path=REFERENCE,
    cfg_weight=0.3,
)

# Knip de generatieve staart af.
samples = wav.squeeze(0)

threshold = 0.015
active = (samples.abs() > threshold).nonzero()

if len(active) > 0:
    last = active[-1].item()

    # Houd nog 80 ms na het laatste duidelijke geluid.
    margin = int(model.sr * 0.08)
    end = min(last + margin, samples.numel())

    samples = samples[:end]

    # Korte fade-out tegen een harde knip.
    fade = int(model.sr * 0.03)

    if samples.numel() > fade:
        samples[-fade:] *= torch.linspace(
            1.0, 0.0, fade, device=samples.device
        )

    wav = samples.unsqueeze(0)

ta.save(OUTPUT, wav, model.sr)

print(f"Gemaakt: {OUTPUT}")
