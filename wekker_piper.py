from datetime import datetime
import subprocess
import sys
import time

import numpy as np
import pyaudio
import openwakeword
from openwakeword.model import Model

RATE = 16000
CHUNK = 1280
THRESHOLD = 0.5
COOLDOWN = 3
WAV = "/tmp/wekker.wav"

paths = [
    p for p in openwakeword.get_pretrained_model_paths("onnx")
    if "alexa" in p.lower()
]

model = Model(
    wakeword_models=[paths[0]],
    inference_framework="onnx",
)

p = pyaudio.PyAudio()

device_index = next(
    i for i in range(p.get_device_count())
    if p.get_device_info_by_index(i)["maxInputChannels"] > 0
    and p.get_device_info_by_index(i)["name"].lower() == "pulse"
)

stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    input_device_index=device_index,
    frames_per_buffer=CHUNK,
)

print("Luisteren. Zeg: ALEXA")
print("Stoppen: Ctrl-C")

last_trigger = 0

try:
    while True:
        raw = stream.read(CHUNK, exception_on_overflow=False)
        audio = np.frombuffer(raw, dtype=np.int16)

        prediction = model.predict(audio)
        score = next(iter(prediction.values()))

        if score >= THRESHOLD and time.monotonic() - last_trigger > COOLDOWN:
            last_trigger = time.monotonic()

            now = datetime.now()
            tekst = f"Het is {now.hour} uur en {now.minute} minuten."

            print(f"\nHerkend ({score:.2f}): {tekst}")

            stream.stop_stream()

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

            stream.start_stream()

except KeyboardInterrupt:
    print("\nGestopt.")
finally:
    stream.close()
    p.terminate()
