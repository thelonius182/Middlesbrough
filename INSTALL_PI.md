# Installatie op Raspberry Pi

## 1. Systeempakketten

```bash
sudo apt update
sudo apt install -y \
  python3-venv \
  python3-dev \
  portaudio19-dev \
  alsa-utils
```

## 2. Python-omgeving

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

## 3. Audio controleren

Microfoons en opname-apparaten:

```bash
arecord -l
```

Afspeelapparaten:

```bash
aplay -l
```

Testopname:

```bash
arecord -f S16_LE -r 16000 -c 1 -d 5 /tmp/mic-test.wav
aplay /tmp/mic-test.wav
```

## 4. Runtime testen

```bash
.venv/bin/python test_linux_runtime.py
```

Hierbij worden op de Raspberry Pi de audiostartlatentie en het volume van de eindpiep beoordeeld.

## 5. Sprekende klok starten

```bash
.venv/bin/python sprekende_klok.py
```

Opdracht:

```text
WHAT TIME IS IT
```

Verwachte volgorde:

1. laag-hoog bevestigingssignaal
2. gesproken tijdmelding
3. eindpiep op het genoemde tijdstip
