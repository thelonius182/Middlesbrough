import math
import subprocess
import tempfile
import wave
from pathlib import Path


def speel_wav(path):
    subprocess.run(
        ["aplay", "-q", str(path)],
        check=True,
    )


def piep(
    frequentie=1000,
    duur_ms=250,
):
    sample_rate = 24000
    duur = duur_ms / 1000
    aantal_samples = int(sample_rate * duur)

    frames = bytearray()

    for i in range(aantal_samples):
        t = i / sample_rate

        waarde = math.sin(
            2 * math.pi * frequentie * t
        )

        sample = int(
            32767 * 0.35 * waarde
        )

        frames += sample.to_bytes(
            2,
            byteorder="little",
            signed=True,
        )

    path = Path(
        tempfile.gettempdir()
    ) / "sprekende_klok_piep.wav"

    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(frames)

    speel_wav(path)
