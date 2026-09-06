from pathlib import Path
import shutil

import torch
import torchaudio as ta


CONTEXT_DIR = Path("minute_context_candidates")
OUTPUT_DIR = Path("minute_candidates")
SELECTED_MINUTES_DIR = Path("samples/minutes")
REJECTED_FILE = Path("samples/rejected.txt")

BACKUP_DIR = Path("minute_candidates_before_reextract")

FRAME_MS = 20
HOP_MS = 10

THRESHOLD = 0.020
MIN_SILENCE_MS = 50
EDGE_SILENCE_MS = 20

# Na de tweede grens moet nog voldoende spraak volgen:
# dat is het woord "precies".
MIN_SPEECH_AFTER_SECOND_MS = 220


def find_silences(x, sr):
    frame = int(sr * FRAME_MS / 1000)
    hop = int(sr * HOP_MS / 1000)

    envelope = (
        x.abs()
        .unfold(0, frame, hop)
        .mean(dim=1)
    )

    silent = envelope < THRESHOLD

    runs = []
    start = None

    for i, value in enumerate(silent.tolist()):
        if value:
            if start is None:
                start = i
        elif start is not None:
            runs.append((start, i))
            start = None

    if start is not None:
        runs.append((start, len(silent)))

    result = []

    for begin, end in runs:
        duration_ms = (end - begin) * HOP_MS

        if duration_ms < MIN_SILENCE_MS:
            continue

        result.append(
            (
                begin * hop / sr,
                end * hop / sr,
                duration_ms,
            )
        )

    return result


def has_speech_after(x, sr, end_s):
    """
    Controleer of er na een stilte nog minstens een korte
    hoeveelheid echte spraak zit. Zo valt eindstilte ná
    'precies' af.
    """
    start_sample = int(end_s * sr)

    if start_sample >= x.numel():
        return False

    tail = x[start_sample:]

    frame = int(sr * FRAME_MS / 1000)
    hop = int(sr * HOP_MS / 1000)

    if tail.numel() < frame:
        return False

    envelope = (
        tail.abs()
        .unfold(0, frame, hop)
        .mean(dim=1)
    )

    active = envelope >= THRESHOLD

    active_ms = active.sum().item() * HOP_MS

    return active_ms >= MIN_SPEECH_AFTER_SECOND_MS


def extract_minute(wav, sr):
    x = wav.mean(dim=0)
    duration = x.numel() / sr

    silences = find_silences(x, sr)

    # Eerste zinsgrens:
    # na "Bij de volgende toon is het drie uur."
    first_candidates = [
        s for s in silences
        if 1.35 <= s[0] <= 2.20
    ]

    if not first_candidates:
        raise RuntimeError(
            f"Eerste grens niet gevonden: {silences}"
        )

    # Neem binnen dit venster de langste stilte.
    first = max(
        first_candidates,
        key=lambda s: s[2],
    )

    # Tweede zinsgrens:
    # moet ná het minuutfragment liggen én er moet daarna
    # nog voldoende spraak volgen ("precies").
    second_candidates = [
        s for s in silences
        if s[0] > first[1] + 0.25
        and s[0] < duration - 0.20
        and has_speech_after(x, sr, s[1])
    ]

    if not second_candidates:
        raise RuntimeError(
            f"Tweede grens niet gevonden: {silences}"
        )

    # De grens vóór "precies" is de laatste bruikbare
    # interne stilte waarvoor nog spraak volgt.
    second = max(
        second_candidates,
        key=lambda s: s[0],
    )

    if second[0] <= first[1]:
        raise RuntimeError(
            f"Ongeldige grensvolgorde: first={first}, second={second}"
        )

    start_s = max(
        first[0],
        first[1] - EDGE_SILENCE_MS / 1000,
    )

    end_s = min(
        second[1],
        second[0] + EDGE_SILENCE_MS / 1000,
    )

    start_sample = int(start_s * sr)
    end_sample = int(end_s * sr)

    fragment = wav[:, start_sample:end_sample].clone()

    fade = min(
        int(sr * 0.010),
        fragment.shape[-1],
    )

    if fade > 0:
        fragment[:, :fade] *= torch.linspace(
            0.0,
            1.0,
            fade,
        )

        fragment[:, -fade:] *= torch.linspace(
            1.0,
            0.0,
            fade,
        )

    return fragment, first, second


def backup_current_candidates():
    if BACKUP_DIR.exists():
        return

    if OUTPUT_DIR.exists():
        shutil.copytree(
            OUTPUT_DIR,
            BACKUP_DIR,
        )

        print(
            f"Backup gemaakt: {BACKUP_DIR}"
        )


def clear_old_minute_selections():
    if SELECTED_MINUTES_DIR.exists():
        for path in SELECTED_MINUTES_DIR.glob("*.wav"):
            path.unlink()

    if REJECTED_FILE.exists():
        lines = REJECTED_FILE.read_text(
            encoding="utf-8-sig"
        ).splitlines()

        keep = [
            line.strip()
            for line in lines
            if line.strip()
            and not line.strip().startswith("minutes/")
        ]

        text = "\n".join(keep)

        if text:
            text += "\n"

        REJECTED_FILE.write_text(
            text,
            encoding="utf-8",
        )

    print(
        "Oude minuutkeuzes en minuut-afkeuringen verwijderd."
    )


def main():
    if not CONTEXT_DIR.exists():
        raise FileNotFoundError(
            f"Contextmap niet gevonden: {CONTEXT_DIR}"
        )

    backup_current_candidates()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    failed = []

    files = sorted(
        CONTEXT_DIR.glob("*.wav")
    )

    print(
        f"Contextbestanden gevonden: {len(files)}"
    )

    for path in files:
        wav, sr = ta.load(path)

        try:
            fragment, first, second = extract_minute(
                wav,
                sr,
            )

            target = OUTPUT_DIR / path.name

            ta.save(
                target,
                fragment,
                sr,
            )

            print(
                f"{path.name}: "
                f"{first[0]:.2f}-{first[1]:.2f} / "
                f"{second[0]:.2f}-{second[1]:.2f}"
            )

        except RuntimeError as error:
            print(
                f"{path.name}: MISLUKT - {error}"
            )

            failed.append(
                (path.name, str(error))
            )

    print()

    if failed:
        print(
            "Niet alle bestanden konden veilig opnieuw worden geknipt."
        )

        for name, error in failed:
            print(
                f"  {name}: {error}"
            )

        print()
        print(
            "Bestaande minuutkeuzes zijn NIET verwijderd."
        )

        return

    print(
        "Alle minuutkandidaten opnieuw geknipt."
    )

    clear_old_minute_selections()

    print()
    print(
        "Klaar. De minuten kunnen opnieuw worden beoordeeld."
    )


if __name__ == "__main__":
    main()
