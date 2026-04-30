# Captador de voz FRUNA

Aplicación de escritorio en Python para escuchar pedidos por voz, separar boletas con **"aparte"**, calcular totales y guardar boletas en TXT.

## Estructura

```
project/
├── main.py
├── speech/
│   └── speech_recognizer.py
├── parser/
│   └── order_parser.py
├── models/
│   ├── product_catalog.py
│   ├── order.py
│   └── receipt_generator.py
└── ui/
    └── app_ui.py
```

## Requisitos

- Python 3.10+
- Sistema con micrófono
- Dependencias: `vosk`, `pyaudio`, `pytest` (para pruebas)

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install vosk pyaudio
```

Descarga un modelo español de Vosk (recomendado `vosk-model-small-es-0.42`) y ubícalo en `project/vosk-model-small-es-0.42`.

## Ejecución

```bash
cd project
python main.py
```

## Mejoras implementadas

- Parser mejorado: admite números en dígitos y palabras (`uno`, `dos`, `tres`, etc.).
- Manejo incremental de boletas: cada `aparte` cierra boleta y conserva texto pendiente sin reprocesar todo.
- Botón de escucha con modo iniciar/detener.
- Cierre manual de boleta pendiente (sin decir "aparte").
- Guardado de historial completo de boletas de la sesión.


## Pruebas

```bash
cd project
pytest -q
```
