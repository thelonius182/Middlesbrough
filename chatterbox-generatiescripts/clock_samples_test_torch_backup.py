from datetime import datetime, timedelta
import time
import winsound

import torch
import torchaudio as ta

from clock_engine import volgende_tien_seconden_grens, sample_paths


OUTPUT = "clock_samples_test.wav"

PAUZE_TUSSEN_DELEN = 0.45
PAUZE_VOOR_PIEP = 1.0

BEEP_FREQUENCY = 1000
BEEP_DURATION_MS = 250



def maak_bericht(paths):
    clips = []
    sample_rate = None

    for path in paths:
        if not path.exists():
            raise FileNotFoundError(
                f"Sample ontbreekt: {path}"
            )

        wav, sr = ta.load(path)

        if sample_rate is None:
            sample_rate = sr
        elif sr != sample_rate:
            raise ValueError(
                f"Afwijkende sample rate: {path}"
            )

        clips.append(wav)

    stilte = torch.zeros(
        1,
        int(sample_rate * PAUZE_TUSSEN_DELEN),
    )

    onderdelen = []

    for i, clip in enumerate(clips):
        if i > 0:
            onderdelen.append(stilte)

        onderdelen.append(clip)

    wav = torch.cat(
        onderdelen,
        dim=-1,
    )

    ta.save(
        OUTPUT,
        wav,
        sample_rate,
    )

    return wav.shape[-1] / sample_rate


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
