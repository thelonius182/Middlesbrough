import numpy as np
import pyaudio
import openwakeword
from openwakeword.model import Model

RATE = 16000
CHUNK = 1280

# Zoek het gedownloade Alexa ONNX-model
paths = [
    p for p in openwakeword.get_pretrained_model_paths("onnx")
    if "alexa" in p.lower()
]

if not paths:
    raise RuntimeError("Alexa-model niet gevonden")

print("Model:", paths[0])

model = Model(
    wakeword_models=[paths[0]],
    inference_framework="onnx",
)

p = pyaudio.PyAudio()

# Gebruik het PulseAudio/PipeWire input-device
device_index = None
for i in range(p.get_device_count()):
    d = p.get_device_info_by_index(i)
    if d["maxInputChannels"] > 0 and d["name"].lower() == "pulse":
        device_index = i
        break

if device_index is None:
    raise RuntimeError("Pulse input-device niet gevonden")

stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=RATE,
    input=True,
    input_device_index=device_index,
    frames_per_buffer=CHUNK,
)

print(f"Luisteren via device {device_index}. Zeg een paar keer: ALEXA")
print("Stoppen: Ctrl-C")

try:
    while True:
        raw = stream.read(CHUNK, exception_on_overflow=False)
        audio = np.frombuffer(raw, dtype=np.int16)

        prediction = model.predict(audio)
        score = next(iter(prediction.values()))

        status = " <<< HERKEND" if score > 0.5 else ""
        print(f"\rscore: {score:0.3f}{status}        ", end="", flush=True)

except KeyboardInterrupt:
    print("\nGestopt.")
finally:
    stream.close()
    p.terminate()
