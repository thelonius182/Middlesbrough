from datetime import datetime
import wave
import winsound

from clock_engine import sample_paths


OUTPUT = "clock_selected_hour_test.wav"

PAUZE_TUSSEN_DELEN = 0.45


def maak_bericht(paths):
    frames = []
    params = None

    for path in paths:
        if not path.exists():
            raise FileNotFoundError(
                f"Sample ontbreekt: {path}"
            )

        with wave.open(str(path), "rb") as wav_file:
            huidige_params = (
                wav_file.getnchannels(),
                wav_file.getsampwidth(),
                wav_file.getframerate(),
            )

            if params is None:
                params = huidige_params
            elif huidige_params != params:
                raise ValueError(
                    f"Afwijkend WAV-formaat: {path}"
                )

            frames.append(
                wav_file.readframes(
                    wav_file.getnframes()
                )
            )

    channels, sample_width, sample_rate = params

    stilte_frames = int(
        sample_rate * PAUZE_TUSSEN_DELEN
    )

    stilte = b"\x00" * (
        stilte_frames
        * channels
        * sample_width
    )

    onderdelen = []

    for i, clip in enumerate(frames):
        if i > 0:
            onderdelen.append(stilte)

        onderdelen.append(clip)

    audio = b"".join(onderdelen)

    with wave.open(OUTPUT, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio)


tijdstip = datetime(
    2026,
    1,
    1,
    10,
    15,
    30,
)

paths = sample_paths(tijdstip)

print("Testtijd:", tijdstip.strftime("%H:%M:%S"))
print("Fragmenten:")

for path in paths:
    print(" ", path)

maak_bericht(paths)

winsound.PlaySound(
    OUTPUT,
    winsound.SND_FILENAME,
)
