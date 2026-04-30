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
├── tests/
│   ├── test_order_parser.py
│   └── test_receipt_generator.py
└── ui/
    └── app_ui.py
```

## Requisitos

- Python 3.10+
- Sistema con micrófono
- Dependencias: `vosk`, `pyaudio`, `pytest`

## Instalación paso a paso

1. Entrar a la carpeta del proyecto:

```bash
cd project
```

2. Crear y activar entorno virtual:

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Configuración del modelo Vosk (MUY IMPORTANTE)

La app busca el modelo en esta ruta **exacta** (relativa a `project/`):

```text
project/vosk-model-small-es-0.42
```

### Dónde debe quedar exactamente

Si estás en la raíz del repositorio (`/workspace/captador-de-voz`), la carpeta final debe ser:

```text
/workspace/captador-de-voz/project/vosk-model-small-es-0.42
```

Y dentro de esa carpeta deben existir archivos del modelo como `am/`, `conf/`, `graph/`, `ivector/`, etc.

### Pasos recomendados

1. Descargar un modelo español de Vosk (por ejemplo: `vosk-model-small-es-0.42`).
2. Descomprimir el archivo.
3. Renombrar la carpeta descomprimida a exactamente:

```text
vosk-model-small-es-0.42
```

4. Mover esa carpeta dentro de `project/`.

### Verificación rápida

Desde la raíz del repositorio:

```bash
test -d project/vosk-model-small-es-0.42 && echo "OK: modelo encontrado" || echo "ERROR: falta el modelo"
```

Si sale `ERROR`, la UI mostrará `Modelo no encontrado` al iniciar escucha.

## Ejecución

```bash
cd project
python main.py
```

## Uso rápido

1. Presiona **Iniciar escucha**.
2. Dicta pedidos, por ejemplo: `2 cocacolas 3 cereales aparte 5 jugos`.
3. Cada vez que digas **aparte**, se cierra una boleta y comienza la siguiente.
4. (Opcional) En **Ajustes**, selecciona el micrófono que quieres usar.
5. Usa **Guardar última boleta** o **Guardar historial** para exportar TXT.

## Pruebas

```bash
cd project
pytest -q
```
