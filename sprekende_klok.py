from datetime import timedelta
from pathlib import Path
import time

import numpy as np
import pyaudio
import sherpa_onnx

from clock_engine import volgende_tien_seconden_grens, sample_paths
from linux_audio import speel_wav
from timing import wacht_tot
from wav_message import maak_bericht


MODEL = "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"
RATE = 16000
CHUNK = 1280
COOLDOWN = 3

BERICHT_WAV = Path("/tmp/spreekbericht.wav")
ACK_WAV = Path("samples/trigger/acknowledged.wav")


kws = sherpa_onnx.KeywordSpotter(
    tokens=f"{MODEL}/tokens.txt",
    encoder=f"{MODEL}/encoder-epoch-13-avg-2-chunk-16-left-64.onnx",
    decoder=f"{MODEL}/decoder-epoch-13-avg-2-chunk-16-left-64.onnx",
    joiner=f"{MODEL}/joiner-epoch-13-avg-2-chunk-16-left-64.onnx",
    keywords_file="keywords.txt",
    keywords_score=3.0,
    keywords_threshold=0.10,
    num_threads=2,
    provider="cpu",
)

stream = kws.create_stream()

p = pyaudio.PyAudio()

input_devices = [
    (i, p.get_device_info_by_index(i))
    for i in range(p.get_device_count())
    if p.get_device_info_by_index(i)["maxInputChannels"] > 0
]

device_index = next(
    (
        i
        for i, info in input_devices
        if "respeaker lite" in info["name"].lower()
    ),
    next(
        (
            i
            for i, info in input_devices
            if info["name"].lower() == "pulse"
        ),
        None,
    ),
)

if device_index is None:
    names = "\n".join(f"{i}: {info['name']}" for i, info in input_devices)
    raise RuntimeError(f"Geen geschikte microfoon gevonden:\n{names}")

print("Microfoon:", p.get_device_info_by_index(device_index)["name"])

mic = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    input_device_index=device_index,
    frames_per_buffer=CHUNK,
)

last_trigger = 0

print("Sprekende klok actief.")
print("Zeg: WHAT TIME IS IT")
print("Stoppen: Ctrl-C")

try:
    while True:
        raw = mic.read(CHUNK, exception_on_overflow=False)

        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32)
        samples /= 32768.0

        stream.accept_waveform(RATE, samples)

        while kws.is_ready(stream):
            kws.decode_stream(stream)
            result = kws.get_result(stream)

            if result and time.monotonic() - last_trigger > COOLDOWN:
                last_trigger = time.monotonic()

                # Niet luisteren terwijl de klok zelf geluid afspeelt.
                mic.stop_stream()

                # Meteen bevestigen dat de opdracht is herkend.
                speel_wav(ACK_WAV)

                # Kies het tijdstip dat bij de eindpiep hoort.
                doeltijd = volgende_tien_seconden_grens()
                paths = sample_paths(doeltijd)

                # Maak één WAV met gesproken melding en eindpiep.
                duur_tot_piep = maak_bericht(
                    paths,
                    BERICHT_WAV,
                    eindpiep=True,
                )

                starttijd = doeltijd - timedelta(seconds=duur_tot_piep)

                print(f"\n{result}")
                print(f"Doeltijd:       {doeltijd.time()}")
                print(f"Start afspelen: {starttijd.time()}")

                wacht_tot(starttijd)
                speel_wav(BERICHT_WAV)

                kws.reset_stream(stream)
                mic.start_stream()

except KeyboardInterrupt:
    print("\nGestopt.")

finally:
    mic.close()
    p.terminate()
