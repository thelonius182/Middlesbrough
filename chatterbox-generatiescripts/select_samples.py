from pathlib import Path
import re
import shutil
import time
import winsound


CANDIDATES_DIR = Path("sample_candidates")
MINUTE_CANDIDATES_DIR = Path("minute_candidates")
BACKUP_DIR = Path("sample_candidates - Copy")
OUTPUT_DIR = Path("samples")

REJECTED_FILE = OUTPUT_DIR / "rejected.txt"
MINUTE_MIGRATION_MARKER = OUTPUT_DIR / ".minutes_context_migrated"

GROUPS = [
    "intro",
    "hours",
    "minutes",
    "seconds",
    "exact",
]

# Deze pilotfragmenten zijn al goedgekeurd.
# "minutes/01" staat hier bewust niet meer bij:
# alle minuten worden opnieuw beoordeeld vanuit minute_candidates.
APPROVED = {
    ("intro", "intro"): "intro_03.wav",
    ("hours", "03"): "03_02.wav",
    ("seconds", "30"): "30_02.wav",
    ("exact", "precies"): "precies_03.wav",
}


def target_path(group, name):
    return OUTPUT_DIR / group / f"{name}.wav"


def migrate_minutes_once():
    """
    Eenmalige overgang van de oude losse minuutkandidaten
    naar de nieuwe context-gegenereerde minuutkandidaten.

    - verwijdert alleen eerder geselecteerde minuten;
    - verwijdert alleen oude minutes/... regels uit rejected.txt;
    - laat uren, seconden, intro en precies ongemoeid;
    - maakt daarna een marker zodat dit bij een volgende start
      niet opnieuw gebeurt.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if MINUTE_MIGRATION_MARKER.exists():
        return

    minutes_dir = OUTPUT_DIR / "minutes"

    if minutes_dir.exists():
        print("Oude minuutkeuzes verwijderen...")

        for path in minutes_dir.glob("*.wav"):
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

    MINUTE_MIGRATION_MARKER.write_text(
        "Nieuwe minuutkandidaten uit minute_candidates actief.\n",
        encoding="utf-8",
    )

    print("Minuten zijn omgezet naar de nieuwe kandidaatset.")


def copy_approved():
    print("Goedgekeurde pilotfragmenten controleren...")

    for (group, name), filename in APPROVED.items():
        source = BACKUP_DIR / group / filename
        target = target_path(group, name)

        if target.exists():
            continue

        if not source.exists():
            raise FileNotFoundError(
                f"Pilotbestand niet gevonden: {source}"
            )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source,
            target,
        )

        print(f"  {source} -> {target}")


def load_rejected():
    if not REJECTED_FILE.exists():
        return set()

    return {
        line.strip()
        for line in REJECTED_FILE.read_text(
            encoding="utf-8-sig"
        ).splitlines()
        if line.strip()
    }


def reject_sample(group, name):
    key = f"{group}/{name}"
    rejected = load_rejected()

    if key in rejected:
        return

    REJECTED_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with REJECTED_FILE.open(
        "a",
        encoding="utf-8",
    ) as f:
        f.write(f"{key}\n")


def candidate_directory(group):
    if group == "minutes":
        return MINUTE_CANDIDATES_DIR

    return CANDIDATES_DIR / group


def find_samples():
    result = []

    for group in GROUPS:
        directory = candidate_directory(group)

        if not directory.exists():
            print(
                f"Waarschuwing: kandidaatmap ontbreekt: {directory}"
            )
            continue

        names = {}

        for path in directory.glob("*.wav"):
            match = re.fullmatch(
                r"(.+)_([0-9]{2})",
                path.stem,
            )

            if not match:
                continue

            name = match.group(1)
            candidate = int(match.group(2))

            names.setdefault(
                name,
                {},
            )[candidate] = path

        def sort_key(item):
            name = item[0]

            if name.isdigit():
                return (0, int(name))

            return (1, name)

        for name, candidates in sorted(
            names.items(),
            key=sort_key,
        ):
            result.append(
                (group, name, candidates)
            )

    return result


def play_candidates(group, name, candidates):
    print()
    print("=" * 60)
    print(f"{group}/{name}")

    numbers = sorted(candidates)

    for i, number in enumerate(numbers):
        path = candidates[number]

        print(
            f"  kandidaat {number}: {path.name}"
        )

        winsound.PlaySound(
            str(path),
            winsound.SND_FILENAME,
        )

        # Twee korte piepjes maken de overgang
        # naar de volgende kandidaat hoorbaar.
        if i < len(numbers) - 1:
            time.sleep(0.35)

            winsound.Beep(700, 100)
            time.sleep(0.10)
            winsound.Beep(700, 100)

            time.sleep(0.55)


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    migrate_minutes_once()
    copy_approved()

    samples = find_samples()
    rejected = load_rejected()

    remaining = [
        sample
        for sample in samples
        if not target_path(
            sample[0],
            sample[1],
        ).exists()
        and f"{sample[0]}/{sample[1]}" not in rejected
    ]

    print()
    print(f"Nog te beoordelen: {len(remaining)}")
    print()
    print("Keuze:")
    print("  1 / 2 / 3 = kandidaat kiezen")
    print("  r         = opnieuw afspelen")
    print("  x         = alle kandidaten afkeuren")
    print("  q         = stoppen")

    for index, (group, name, candidates) in enumerate(
        remaining,
        start=1,
    ):
        while True:
            print()
            print(
                f"[{index}/{len(remaining)}]"
            )

            play_candidates(
                group,
                name,
                candidates,
            )

            keuze = input(
                "Kies 1, 2, 3, r, x of q: "
            ).strip().lower()

            if keuze == "q":
                print()
                print(
                    "Gestopt. Bij de volgende start "
                    "gaat de selectie verder."
                )
                return

            if keuze == "r":
                continue

            if keuze == "x":
                reject_sample(
                    group,
                    name,
                )

                print(
                    f"Afgekeurd: {group}/{name}"
                )
                break

            if keuze not in ("1", "2", "3"):
                print("Ongeldige keuze.")
                continue

            number = int(keuze)

            if number not in candidates:
                print(
                    f"Kandidaat {number} bestaat niet."
                )
                continue

            source = candidates[number]
            target = target_path(
                group,
                name,
            )

            target.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            shutil.copy2(
                source,
                target,
            )

            print(
                f"Gekozen: {source.name} -> {target}"
            )

            break

    print()
    print("Alle beschikbare samples zijn beoordeeld.")


if __name__ == "__main__":
    main()
