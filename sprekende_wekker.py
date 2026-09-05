from datetime import datetime
import subprocess
import sys
import time

import numpy as np
import pyaudio
import sherpa_onnx

def tijdtekst(uur, minuut, seconde):
    minuut_eenheid = "minuut" if minuut == 1 else "minuten"
    seconde_eenheid = "seconde" if seconde == 1 else "seconden"

    return (
        f"Bij de volgende toon is het {uur} uur, "
        f"{minuut} {minuut_eenheid} en "
        f"{seconde} {seconde_eenheid}."
    )

MODEL = "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"
RATE = 16000
CHUNK = 1280
WAV = "/tmp/wekker.wav"
COOLDOWN = 3

kws = sherpa_onnx.KeywordSpotter(
    tokens=f"{MODEL}/tokens.txt",
    encoder=f"{MODEL}/encoder-epoch-13-avg-2-chunk-16-left-64.onnx",
    decoder=f"{MODEL}/decoder-epoch-13-avg-2-chunk-16-left-64.onnx",
    joiner=f"{MODEL}/joiner-epoch-13-avg-2-chunk-16-left-64.onnx",
    keywords_file="keywords.txt",
    keywords_threshold=0.15,
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
        i for i, info in input_devices
        if "respeaker lite" in info["name"].lower()
    ),
    next(
        (
            i for i, info in input_devices
            if info["name"].lower() == "pulse"
        ),
        None,
    ),
)

if device_index is None:
    names = "\n".join(
        f"{i}: {info['name']}"
        for i, info in input_devices
    )
    raise RuntimeError(f"Geen geschikte microfoon gevonden:\n{names}")

print(
    "Microfoon:",
    p.get_device_info_by_index(device_index)["name"],
)

mic = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    input_device_index=device_index,
    frames_per_buffer=CHUNK,
)

last_trigger = 0

print("Sprekende wekker actief.")
print("Zeg: HELLO CLOCK")
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

            if (
                result
                and time.monotonic() - last_trigger > COOLDOWN
            ):
                last_trigger = time.monotonic()

                now = datetime.now()
                tekst = tijdtekst(now.hour, now.minute, now.second)

                print(f"\n{result}: {tekst}")

                # Niet luisteren terwijl de wekker zelf praat.
                mic.stop_stream()

                subprocess.run(
                    [
                        sys.executable,
                        "-m", "piper",
                        "-m", "nl_NL-alex-medium",
                        "-f", WAV,
                        "--", tekst,
                    ],
                    check=True,
                )

                subprocess.run(["aplay", WAV], check=True)

                kws.reset_stream(stream)
                mic.start_stream()

except KeyboardInterrupt:
    print("\nGestopt.")

finally:
    mic.close()
    p.terminate()
