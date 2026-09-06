from datetime import datetime, timedelta
import time
import winsound

import wave

from clock_engine import volgende_tien_seconden_grens, sample_paths


OUTPUT = "clock_samples_test.wav"

PAUZE_TUSSEN_DELEN = 0.45
PAUZE_VOOR_PIEP = 1.0

BEEP_FREQUENCY = 1000
BEEP_DURATION_MS = 250



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

    frame_count = len(audio) // (
        channels * sample_width
    )

    return frame_count / sample_rate

def wacht_tot(tijdstip):
    while True:
        resterend = (
            tijdstip - datetime.now()
        ).total_seconds()

        if resterend <= 0:
            return

        if resterend > 0.1:
            time.sleep(
                min(
                    0.05,
                    resterend - 0.1,
                )
            )
        else:
            while datetime.now() < tijdstip:
                pass

            return


doeltijd = volgende_tien_seconden_grens()
paths = sample_paths(doeltijd)

print(
    "Doeltijd:",
    doeltijd.strftime("%H:%M:%S"),
)

print("Fragmenten:")

for path in paths:
    print(" ", path)

audio_duur = maak_bericht(paths)

print(
    f"Audio: {audio_duur:.2f} s"
)

start_afspelen = doeltijd - timedelta(
    seconds=audio_duur + PAUZE_VOOR_PIEP
)

print(
    "Start afspelen:",
    start_afspelen.strftime("%H:%M:%S.%f"),
)

wacht_tot(start_afspelen)

winsound.PlaySound(
    OUTPUT,
    winsound.SND_FILENAME,
)

wacht_tot(doeltijd)

piep_start = datetime.now()

winsound.Beep(
    BEEP_FREQUENCY,
    BEEP_DURATION_MS,
)

print(
    "PIEP gestart:",
    piep_start.strftime("%H:%M:%S.%f"),
)
