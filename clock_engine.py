from datetime import datetime, timedelta
from pathlib import Path


SAMPLES = Path("samples")
# SAMPLES = Path("samples_pcm16")
LEAD_SECONDS = 15


def volgende_tien_seconden_grens():
    kandidaat = datetime.now() + timedelta(
        seconds=LEAD_SECONDS
    )

    if kandidaat.microsecond:
        kandidaat = (
            kandidaat.replace(microsecond=0)
            + timedelta(seconds=1)
        )

    extra = (-kandidaat.second) % 10

    return kandidaat + timedelta(seconds=extra)


def sample_paths(tijdstip):
    uur = tijdstip.hour
    minuut = tijdstip.minute
    seconde = tijdstip.second

    paths = [
        SAMPLES / "intro" / "intro.wav",
        SAMPLES / "hours" / f"{uur:02d}.wav",
    ]

    if minuut == 0 and seconde == 0:
        paths.append(
            SAMPLES / "exact" / "precies.wav"
        )
        return paths

    paths.append(
        SAMPLES / "minutes" / f"{minuut:02d}.wav"
    )

    if seconde == 0:
        paths.append(
            SAMPLES / "exact" / "precies.wav"
        )
    else:
        paths.append(
            SAMPLES / "seconds" / f"{seconde:02d}.wav"
        )

    return paths
