from datetime import datetime, timedelta

from clock_engine import volgende_tien_seconden_grens, sample_paths
from timing import wacht_tot
from wav_message import maak_bericht
from windows_audio import speel_wav, piep


OUTPUT = "clock_samples_test.wav"

PAUZE_TUSSEN_DELEN = 0.45
PAUZE_VOOR_PIEP = 1.0

BEEP_FREQUENCY = 1000
BEEP_DURATION_MS = 250


doeltijd = volgende_tien_seconden_grens()
paths = sample_paths(doeltijd)

print(
    "Doeltijd:",
    doeltijd.strftime("%H:%M:%S"),
)

print("Fragmenten:")

for path in paths:
    print(" ", path)

audio_duur = maak_bericht(
    paths,
    OUTPUT,
    PAUZE_TUSSEN_DELEN,
)

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

speel_wav(OUTPUT)

wacht_tot(doeltijd)

piep_start = datetime.now()

piep(
    BEEP_FREQUENCY,
    BEEP_DURATION_MS,
)

print(
    "PIEP gestart:",
    piep_start.strftime("%H:%M:%S.%f"),
)
