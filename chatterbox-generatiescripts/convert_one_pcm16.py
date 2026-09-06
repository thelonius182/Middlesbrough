from pathlib import Path

import torchaudio as ta


SOURCE = Path("samples/hours/00.wav")
OUTPUT = Path("00_pcm16_test.wav")

wav, sample_rate = ta.load(SOURCE)

ta.save(
    OUTPUT,
    wav,
    sample_rate,
    encoding="PCM_S",
    bits_per_sample=16,
)

print(f"Gemaakt: {OUTPUT}")
