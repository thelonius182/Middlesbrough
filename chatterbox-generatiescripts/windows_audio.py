import winsound


def speel_wav(path):
    winsound.PlaySound(
        str(path),
        winsound.SND_FILENAME,
    )


def piep(
    frequentie=1000,
    duur_ms=250,
):
    winsound.Beep(
        frequentie,
        duur_ms,
    )
