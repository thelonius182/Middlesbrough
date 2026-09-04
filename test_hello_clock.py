import numpy as np
import pyaudio
import sherpa_onnx

MODEL = "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"
RATE = 16000
CHUNK = 1280

kws = sherpa_onnx.KeywordSpotter(
    tokens=f"{MODEL}/tokens.txt",
    encoder=f"{MODEL}/encoder-epoch-13-avg-2-chunk-16-left-64.onnx",
    decoder=f"{MODEL}/decoder-epoch-13-avg-2-chunk-16-left-64.onnx",
    joiner=f"{MODEL}/joiner-epoch-13-avg-2-chunk-16-left-64.onnx",
    keywords_file="keywords.txt",
    num_threads=2,
    keywords_threshold=0.15,
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

print("Luisteren. Zeg: HELLO CLOCK")
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

            if result:
                print(f"\nHERKEND: {result}")
                kws.reset_stream(stream)

except KeyboardInterrupt:
    print("\nGestopt.")

finally:
    mic.close()
    p.terminate()
