from pathlib import Path
import winsound


HOURS_DIR = Path("samples/hours")


def main():
    for uur in range(24):
        path = HOURS_DIR / f"{uur:02d}.wav"

        if not path.exists():
            raise FileNotFoundError(
                f"Sample ontbreekt: {path}"
            )

        print()
        print(f"{uur:02d}.wav")

        winsound.PlaySound(
            str(path),
            winsound.SND_FILENAME,
        )

        input("Enter voor volgende...")


if __name__ == "__main__":
    main()
