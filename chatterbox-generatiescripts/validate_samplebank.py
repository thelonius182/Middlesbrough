from pathlib import Path
import wave


SAMPLES = Path("samples")


def verwachte_bestanden():
    files = {
        SAMPLES / "intro" / "intro.wav",
        SAMPLES / "exact" / "precies.wav",
    }

    files.update(
        SAMPLES / "hours" / f"{uur:02d}.wav"
        for uur in range(24)
    )

    files.update(
        SAMPLES / "minutes" / f"{minuut:02d}.wav"
        for minuut in range(60)
    )

    files.update(
        SAMPLES / "seconds" / f"{seconde:02d}.wav"
        for seconde in (10, 20, 30, 40, 50)
    )

    return files


def main():
    expected = verwachte_bestanden()
    actual = set(SAMPLES.rglob("*.wav"))

    missing = sorted(expected - actual)
    extra = sorted(actual - expected)

    errors = []

    if missing:
        errors.append("Ontbrekende bestanden:")
        errors.extend(f"  {path}" for path in missing)

    if extra:
        errors.append("Onverwachte bestanden:")
        errors.extend(f"  {path}" for path in extra)

    reference_format = None

    for path in sorted(expected & actual):
        try:
            with wave.open(str(path), "rb") as wav_file:
                fmt = (
                    wav_file.getnchannels(),
                    wav_file.getsampwidth(),
                    wav_file.getframerate(),
                    wav_file.getcomptype(),
                )
        except (wave.Error, EOFError) as exc:
            errors.append(
                f"Kan WAV niet lezen: {path}: {exc}"
            )
            continue

        channels, sample_width, sample_rate, comp_type = fmt

        if sample_width != 2:
            errors.append(
                f"Niet PCM16: {path} "
                f"(sample width = {sample_width * 8} bit)"
            )

        if comp_type != "NONE":
            errors.append(
                f"Gecomprimeerde WAV: {path} "
                f"(type = {comp_type})"
            )

        if reference_format is None:
            reference_format = fmt
        elif fmt != reference_format:
            errors.append(
                f"Afwijkend WAV-formaat: {path} "
                f"{fmt} != {reference_format}"
            )

    print(f"Verwacht: {len(expected)} WAV-bestanden")
    print(f"Gevonden: {len(actual)} WAV-bestanden")

    if reference_format is not None:
        channels, sample_width, sample_rate, comp_type = reference_format
        print(
            "Formaat:",
            f"{channels} kanaal/kanelen, "
            f"{sample_width * 8}-bit PCM, "
            f"{sample_rate} Hz, "
            f"compressie={comp_type}",
        )

    if errors:
        print()
        print("FOUT:")
        for error in errors:
            print(error)
        raise SystemExit(1)

    print()
    print("OK: samplebank is compleet en technisch consistent.")


if __name__ == "__main__":
    main()
