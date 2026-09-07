import math
import wave


def maak_bericht(
    paths,
    output,
    pauze_tussen_delen=0.45,
    eindpiep=False,
    piep_frequentie=1000,
    piep_duur=0.25,
    piep_volume=0.35,
):
    frames = []
    params = None

    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Sample ontbreekt: {path}")

        with wave.open(str(path), "rb") as wav_file:
            huidige_params = (
                wav_file.getnchannels(),
                wav_file.getsampwidth(),
                wav_file.getframerate(),
            )

            if params is None:
                params = huidige_params
            elif huidige_params != params:
                raise ValueError(f"Afwijkend WAV-formaat: {path}")

            frames.append(wav_file.readframes(wav_file.getnframes()))

    channels, sample_width, sample_rate = params

    stilte_frames = int(sample_rate * pauze_tussen_delen)
    stilte = b"\x00" * (stilte_frames * channels * sample_width)

    onderdelen = []

    for i, clip in enumerate(frames):
        if i > 0:
            onderdelen.append(stilte)

        onderdelen.append(clip)

    audio = b"".join(onderdelen)

    # Dit is de duur tot het begin van de eindpiep.
    frames_tot_piep = len(audio) // (channels * sample_width)

    if eindpiep:
        aantal_piepframes = int(sample_rate * piep_duur)
        piep = bytearray()

        for i in range(aantal_piepframes):
            t = i / sample_rate
            waarde = math.sin(2 * math.pi * piep_frequentie * t)
            sample = int(32767 * piep_volume * waarde)

            frame = sample.to_bytes(
                2,
                byteorder="little",
                signed=True,
            )

            piep += frame * channels

        audio += piep

    with wave.open(str(output), "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio)

    return frames_tot_piep / sample_rate
