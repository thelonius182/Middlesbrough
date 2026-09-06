import wave


def maak_bericht(
    paths,
    output,
    pauze_tussen_delen=0.45,
):
    frames = []
    params = None

    for path in paths:
        if not path.exists():
            raise FileNotFoundError(
                f"Sample ontbreekt: {path}"
            )

        with wave.open(str(path), "rb") as wav_file:
            huidige_params = (
                wav_file.getnchannels(),
                wav_file.getsampwidth(),
                wav_file.getframerate(),
            )

            if params is None:
                params = huidige_params
            elif huidige_params != params:
                raise ValueError(
                    f"Afwijkend WAV-formaat: {path}"
                )

            frames.append(
                wav_file.readframes(
                    wav_file.getnframes()
                )
            )

    channels, sample_width, sample_rate = params

    stilte_frames = int(
        sample_rate * pauze_tussen_delen
    )

    stilte = b"\x00" * (
        stilte_frames
        * channels
        * sample_width
    )

    onderdelen = []

    for i, clip in enumerate(frames):
        if i > 0:
            onderdelen.append(stilte)

        onderdelen.append(clip)

    audio = b"".join(onderdelen)

    with wave.open(str(output), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio)

    frame_count = len(audio) // (
        channels * sample_width
    )

    return frame_count / sample_rate
