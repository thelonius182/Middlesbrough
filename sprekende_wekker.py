from datetime import datetime
import subprocess
import sys
import time

import numpy as np
import pyaudio
import sherpa_onnx

def tijdtekst(uur, minuut):
    volgend_uur = (uur + 1) % 24

    if minuut == 0:
        return f"Het is {uur} uur."
    if minuut == 15:
        return f"Het is kwart over {uur}."
    if minuut == 30:
        return f"Het is half {volgend_uur}."
    if minuut == 45:
        return f"Het is kwart voor {volgend_uur}."
    if minuut < 15:
        return f"Het is {minuut} over {uur}."
    if minuut < 30:
        return f"Het is {30 - minuut} voor half {volgend_uur}."
    if minuut < 45:
        return f"Het is {minuut - 30} over half {volgend_uur}."
    return f"Het is {60 - minuut} voor {volgend_uur}."


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

device_index = next(
    i for i in range(p.get_device_count())
    if p.get_device_info_by_index(i)["maxInputChannels"] > 0
    and p.get_device_info_by_index(i)["name"].lower() == "pulse"
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
                tekst = tijdtekst(now.hour, now.minute)

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
