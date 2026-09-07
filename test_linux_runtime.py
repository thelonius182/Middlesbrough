from datetime import timedelta
from pathlib import Path

from clock_engine import volgende_tien_seconden_grens, sample_paths
from wav_message import maak_bericht
from timing import wacht_tot
from linux_audio import speel_wav


OUTPUT = Path("/tmp/spreekbericht.wav")

doeltijd = volgende_tien_seconden_grens()
paths = sample_paths(doeltijd)

duur_tot_piep = maak_bericht(
    paths,
    OUTPUT,
    eindpiep=True,
)

starttijd = doeltijd - timedelta(seconds=duur_tot_piep)

print(f"Doeltijd:       {doeltijd.time()}")
print(f"Tot piep:       {duur_tot_piep:.3f} s")
print(f"Start afspelen: {starttijd.time()}")

wacht_tot(starttijd)
speel_wav(OUTPUT)
