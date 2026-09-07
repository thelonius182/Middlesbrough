from __future__ import annotations

import importlib
import py_compile
import shutil
import sys
import wave
from pathlib import Path


PROJECT = Path(__file__).resolve().parent
SAMPLES = PROJECT / "samples"
MODEL = PROJECT / "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"

EXPECTED_SAMPLE_FILES = {
    SAMPLES / "intro" / "intro.wav",
    SAMPLES / "exact" / "precies.wav",
    SAMPLES / "trigger" / "acknowledged.wav",
    *(SAMPLES / "hours" / f"{i:02d}.wav" for i in range(24)),
    *(SAMPLES / "minutes" / f"{i:02d}.wav" for i in range(60)),
    *(SAMPLES / "seconds" / f"{i:02d}.wav" for i in (10, 20, 30, 40, 50)),
}

REQUIRED_MODEL_FILES = (
    "tokens.txt",
    "encoder-epoch-13-avg-2-chunk-16-left-64.onnx",
    "decoder-epoch-13-avg-2-chunk-16-left-64.onnx",
    "joiner-epoch-13-avg-2-chunk-16-left-64.onnx",
)

PYTHON_MODULES = (
    "clock_engine.py",
    "wav_message.py",
    "timing.py",
    "linux_audio.py",
    "sprekende_klok.py",
    "test_linux_runtime.py",
)

PYTHON_PACKAGES = (
    "numpy",
    "pyaudio",
    "sherpa_onnx",
)

failures = 0


def ok(message: str) -> None:
    print(f"OK:   {message}")


def fail(message: str) -> None:
    global failures
    failures += 1
    print(f"FOUT: {message}")


def check_samples() -> None:
    if not SAMPLES.is_dir():
        fail(f"samplemap ontbreekt: {SAMPLES}")
        return

    actual = set(SAMPLES.rglob("*.wav"))

    missing = sorted(EXPECTED_SAMPLE_FILES - actual)
    extra = sorted(actual - EXPECTED_SAMPLE_FILES)

    if missing:
        for path in missing:
            fail(f"sample ontbreekt: {path.relative_to(PROJECT)}")
    else:
        ok(f"alle {len(EXPECTED_SAMPLE_FILES)} verwachte WAV-bestanden aanwezig")

    if extra:
        for path in extra:
            fail(f"onverwachte WAV: {path.relative_to(PROJECT)}")

    bad_format = []

    for path in sorted(EXPECTED_SAMPLE_FILES & actual):
        try:
            with wave.open(str(path), "rb") as wav:
                current = (
                    wav.getnchannels(),
                    wav.getsampwidth(),
                    wav.getframerate(),
                    wav.getcomptype(),
                )
        except (wave.Error, OSError) as exc:
            bad_format.append((path, f"niet leesbaar: {exc}"))
            continue

        expected = (1, 2, 24000, "NONE")
        if current != expected:
            bad_format.append((path, str(current)))

    if bad_format:
        for path, details in bad_format:
            fail(f"afwijkend WAV-formaat: {path.relative_to(PROJECT)} ({details})")
    elif not missing:
        ok("alle WAV-bestanden zijn mono, PCM16, 24 kHz")


def check_model() -> None:
    if not MODEL.is_dir():
        fail(f"KWS-modelmap ontbreekt: {MODEL.name}")
        return

    missing = [name for name in REQUIRED_MODEL_FILES if not (MODEL / name).is_file()]

    if missing:
        for name in missing:
            fail(f"KWS-modelbestand ontbreekt: {MODEL.name}/{name}")
    else:
        ok("KWS-modelbestanden aanwezig")


def check_keywords() -> None:
    keywords = PROJECT / "keywords.txt"
    keywords_raw = PROJECT / "keywords_raw.txt"

    if not keywords.is_file():
        fail("keywords.txt ontbreekt")
    else:
        text = keywords.read_text(encoding="utf-8").strip()
        if "@WHAT_TIME_IS_IT" not in text:
            fail("keywords.txt bevat @WHAT_TIME_IS_IT niet")
        else:
            ok("keywords.txt bevat WHAT_TIME_IS_IT")

    if not keywords_raw.is_file():
        fail("keywords_raw.txt ontbreekt")
    else:
        text = keywords_raw.read_text(encoding="utf-8").strip()
        if text != "WHAT TIME IS IT @WHAT_TIME_IS_IT":
            fail(f"onverwachte inhoud keywords_raw.txt: {text!r}")
        else:
            ok("keywords_raw.txt klopt")


def check_python_packages() -> None:
    for package in PYTHON_PACKAGES:
        try:
            module = importlib.import_module(package)
        except Exception as exc:
            fail(f"Python-package {package} importeert niet: {exc}")
            continue

        version = getattr(module, "__version__", None)
        if version:
            ok(f"Python-package {package} importeert ({version})")
        else:
            ok(f"Python-package {package} importeert")


def check_audio_tools() -> None:
    for command in ("aplay", "arecord"):
        path = shutil.which(command)
        if path is None:
            fail(f"{command} niet gevonden")
        else:
            ok(f"{command} gevonden: {path}")


def check_python_files() -> None:
    for name in PYTHON_MODULES:
        path = PROJECT / name

        if not path.is_file():
            fail(f"Python-bestand ontbreekt: {name}")
            continue

        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            fail(f"compilefout in {name}: {exc.msg}")
        else:
            ok(f"{name} compileert")


def main() -> int:
    print("Sprekende klok runtime-check")
    print(f"Project: {PROJECT}")
    print(f"Python:  {sys.version.split()[0]}")
    print()

    check_samples()
    check_model()
    check_keywords()
    check_python_packages()
    check_audio_tools()
    check_python_files()

    print()

    if failures:
        print(f"RESULTAAT: {failures} fout(en)")
        return 1

    print("RESULTAAT: alles OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
