from pathlib import Path

import torchaudio as ta


SOURCE_ROOT = Path("samples")
TARGET_ROOT = Path("samples_pcm16")


def convert_file(source: Path, target: Path):
    wav, sample_rate = ta.load(source)

    target.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    ta.save(
        target,
        wav,
        sample_rate,
        encoding="PCM_S",
        bits_per_sample=16,
    )


def main():
    wav_files = sorted(
        SOURCE_ROOT.rglob("*.wav")
    )

    if not wav_files:
        raise FileNotFoundError(
            f"Geen WAV-bestanden gevonden onder {SOURCE_ROOT}"
        )

    for source in wav_files:
        relative = source.relative_to(
            SOURCE_ROOT
        )
        target = TARGET_ROOT / relative

        convert_file(
            source,
            target,
        )

        print(
            f"{source} -> {target}"
        )

    print()
    print(
        f"Klaar: {len(wav_files)} bestanden geconverteerd."
    )


if __name__ == "__main__":
    main()
