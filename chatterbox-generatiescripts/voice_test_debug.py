from datetime import datetime, timedelta
import time
import winsound

import torch
import torchaudio as ta

from chatterbox.mtl_tts import ChatterboxMultilingualTTS


REFERENCE = "reference.wav"
OUTPUT = "klok_test.wav"

CFG_WEIGHT = 0.3
LEAD_SECONDS = 30
PAUZE_TUSSEN_DELEN = 0.45
PAUZE_VOOR_PIEP = 1.0

BEEP_FREQUENCY = 1000
BEEP_DURATION_MS = 250


def getal(n):
    klein = [
        "nul", "één", "twee", "drie", "vier",
        "vijf", "zes", "zeven", "acht", "negen",
        "tien", "elf", "twaalf", "dertien", "veertien",
        "vijftien", "zestien", "zeventien", "achttien", "negentien",
    ]

    if n < 20:
        return klein[n]

    tientallen = {
        20: "twintig",
        30: "dertig",
        40: "veertig",
        50: "vijftig",
    }

    if n in tientallen:
        return tientallen[n]

    eenheden = {
        1: "eenen",
        2: "tweeën",
        3: "drieën",
        4: "vieren",
        5: "vijfen",
        6: "zesen",
        7: "zevenen",
        8: "achten",
        9: "negenen",
    }

    tiental = (n // 10) * 10
    eenheid = n % 10

    return eenheden[eenheid] + tientallen[tiental]


def volgende_tien_seconden_grens():
    kandidaat = datetime.now() + timedelta(seconds=LEAD_SECONDS)

    if kandidaat.microsecond:
        kandidaat = kandidaat.replace(microsecond=0) + timedelta(seconds=1)

    extra = (-kandidaat.second) % 10
    return kandidaat + timedelta(seconds=extra)


def tijdsdelen(tijdstip):
    minuut = tijdstip.minute
    seconde = tijdstip.second

    minuut_woord = "minuut" if minuut == 1 else "minuten"
    seconde_woord = "seconde" if seconde == 1 else "seconden"

    delen = [
        f"Bij de volgende toon is het {getal(tijdstip.hour)} uur",
    ]

    if minuut == 0 and seconde == 0:
        delen.append("precies")
        return delen

    delen.append(
        f"{getal(minuut)} {minuut_woord}"
    )

    if seconde == 0:
        delen.append("precies")
    else:
        delen.append(
            f"en {getal(seconde)} {seconde_woord}"
        )

    return delen


def trim_fragment(clip, sr):
    x = clip.squeeze(0)

    frame = int(sr * 0.020)
    hop = int(sr * 0.010)

    if x.numel() < frame:
        return clip.cpu()

    envelope = (
        x.abs()
        .unfold(0, frame, hop)
        .mean(dim=1)
    )

    threshold = max(
        0.004,
        envelope.max().item() * 0.05,
    )

    actief = (envelope > threshold).nonzero()

    if len(actief) == 0:
        return clip.cpu()

    laatste_frame = actief[-1].item()
    einde = laatste_frame * hop + frame

    # Laat 30 ms na het laatste actieve frame staan.
    einde = min(
        einde + int(sr * 0.030),
        x.numel(),
    )

    x = x[:einde].clone()

    # Korte fade-out om een harde knip te voorkomen.
    fade = min(
        int(sr * 0.025),
        x.numel(),
    )

    if fade > 0:
        x[-fade:] *= torch.linspace(
            1.0,
            0.0,
            fade,
            device=x.device,
        )

    return x.unsqueeze(0).cpu()


def wacht_tot(tijdstip):
    while True:
        resterend = (tijdstip - datetime.now()).total_seconds()

        if resterend <= 0:
            return

        if resterend > 0.1:
            time.sleep(min(0.05, resterend - 0.1))
        else:
            while datetime.now() < tijdstip:
                pass
            return


print("Model laden...")

model = ChatterboxMultilingualTTS.from_pretrained(
    device="cuda",
)

doeltijd = volgende_tien_seconden_grens()
delen = tijdsdelen(doeltijd)

print("Doeltijd:", doeltijd.strftime("%H:%M:%S"))
print("Tekst:", ". ".join(delen) + ".")

start = time.perf_counter()

clips = []

for deel in delen:
    print("Genereren:", deel)

    clip = model.generate(
        deel,
        language_id="nl",
        audio_prompt_path=REFERENCE,
        cfg_weight=CFG_WEIGHT,
    )

    trimmed = trim_fragment(clip, model.sr)

    clips.append(trimmed)

    ta.save(
        f"debug_fragment_{len(clips)}.wav",
        trimmed,
        model.sr,
    )

stilte = torch.zeros(
    1,
    int(model.sr * PAUZE_TUSSEN_DELEN),
)

onderdelen = []

for i, clip in enumerate(clips):
    if i > 0:
        onderdelen.append(stilte)

    onderdelen.append(clip)

wav = torch.cat(onderdelen, dim=-1)

synthese_tijd = time.perf_counter() - start
audio_duur = wav.shape[-1] / model.sr

print(f"Synthese: {synthese_tijd:.2f} s")
print(f"Audio:     {audio_duur:.2f} s")

ta.save(OUTPUT, wav, model.sr)

start_afspelen = doeltijd - timedelta(
    seconds=audio_duur + PAUZE_VOOR_PIEP
)

if datetime.now() >= start_afspelen:
    print("Waarschuwing: synthese was te laat voor de geplande afspeeltijd.")
else:
    wacht_tot(start_afspelen)

winsound.PlaySound(
    OUTPUT,
    winsound.SND_FILENAME,
)

wacht_tot(doeltijd)

piep_start = datetime.now()

winsound.Beep(
    BEEP_FREQUENCY,
    BEEP_DURATION_MS,
)

print("PIEP gestart:", piep_start.strftime("%H:%M:%S.%f"))
