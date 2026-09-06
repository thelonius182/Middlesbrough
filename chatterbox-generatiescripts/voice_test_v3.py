from datetime import datetime, timedelta
import time
import winsound
import torch

import torchaudio as ta

from chatterbox.mtl_tts import ChatterboxMultilingualTTS

REFERENCE = "reference.wav"
OUTPUT = "klok_test.wav"

CFG_WEIGHT = 0.3
LEAD_SECONDS = 15
BEEP_FREQUENCY = 1000
BEEP_DURATION_MS = 250
PAUZE_VOOR_PIEP = 1.0
PAUZE_TUSSEN_DELEN = 0.45
LEAD_SECONDS = 30


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

    # Naar de eerstvolgende hele seconde.
    if kandidaat.microsecond:
        kandidaat = kandidaat.replace(microsecond=0) + timedelta(seconds=1)

    # Daarna naar 00, 10, 20, 30, 40 of 50 seconden.
    extra = (-kandidaat.second) % 10
    return kandidaat + timedelta(seconds=extra)


def tijdtekst(tijdstip):
    minuut = tijdstip.minute
    seconde = tijdstip.second

    minuut_woord = "minuut" if minuut == 1 else "minuten"
    seconde_woord = "seconde" if seconde == 1 else "seconden"

    return (
        f"Bij de volgende toon is het {getal(tijdstip.hour)} uur. "
        f"{getal(minuut)} {minuut_woord}. "
        f"En {getal(seconde)} {seconde_woord}."
    )


print("Model laden...")

model = ChatterboxMultilingualTTS.from_pretrained(
    device="cuda",
)

doeltijd = volgende_tien_seconden_grens()
tekst = tijdtekst(doeltijd)

print("Doeltijd:", doeltijd.strftime("%H:%M:%S"))
print("Tekst:", tekst)

start = time.perf_counter()

delen = [
    f"Bij de volgende toon is het {getal(doeltijd.hour)} uur",
    f"{getal(doeltijd.minute)} minuten",
    f"en {getal(doeltijd.second)} seconden",
]

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

    clips.append(clip.cpu())

stilte = torch.zeros(
    1,
    int(model.sr * PAUZE_TUSSEN_DELEN),
)

wav = torch.cat(
    [
        clips[0],
        stilte,
        clips[1],
        stilte,
        clips[2],
    ],
    dim=-1,
)

synthese_tijd = time.perf_counter() - start

print(f"Synthese: {synthese_tijd:.2f} s")

synthese_tijd = time.perf_counter() - start
audio_duur = wav.shape[-1] / model.sr

print(f"Synthese: {synthese_tijd:.2f} s")
print(f"Audio:     {audio_duur:.2f} s")

ta.save(OUTPUT, wav, model.sr)

audio_duur = wav.shape[-1] / model.sr
print(f"Audio:     {audio_duur:.2f} s")

# Zorg dat de gesproken melding precies PAUZE_VOOR_PIEP
# seconden vóór de aangekondigde tijd eindigt.
start_afspelen = doeltijd - timedelta(
    seconds=audio_duur + PAUZE_VOOR_PIEP
)

while datetime.now() < start_afspelen:
    resterend = (start_afspelen - datetime.now()).total_seconds()
    time.sleep(min(0.05, max(0.001, resterend)))

winsound.PlaySound(
    OUTPUT,
    winsound.SND_FILENAME,
)

# Wachten tot vlak voor het aangekondigde tijdstip.
while True:
    resterend = (doeltijd - datetime.now()).total_seconds()

    if resterend <= 0.1:
        break

    time.sleep(min(resterend - 0.1, 0.05))

# Laatste fractie niet aan Windows sleep() overlaten.
while datetime.now() < doeltijd:
    pass

winsound.Beep(
    BEEP_FREQUENCY,
    BEEP_DURATION_MS,
)

print("PIEP:", datetime.now().strftime("%H:%M:%S.%f"))