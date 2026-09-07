# Installatie op Raspberry Pi

## 1. Project en KWS-model kopiëren

Kopieer de projectmap vanaf de Ubuntu-VM naar de Raspberry Pi.

De volgende modelmap staat niet in Git en moet expliciet worden meegekopieerd:

```text
sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20/
```

Het archiefbestand:

```text
sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20.tar.bz2
```

is niet nodig op de Raspberry Pi.

## 2. Systeempakketten

```bash
sudo apt update
sudo apt install -y \
  python3-venv \
  python3-dev \
  portaudio19-dev \
  alsa-utils
```

## 3. Python-omgeving

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

## 4. Audio controleren

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

## 5. Runtime testen

```bash
.venv/bin/python test_linux_runtime.py
```

Hierbij worden op de Raspberry Pi de audiostartlatentie en het volume van de eindpiep beoordeeld.

## 6. Sprekende klok starten

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
