# NovaSub AI 🤖

**NovaSub** es un editor de subtítulos de próxima generación que utiliza **Whisper** para generar propuestas de timing automáticas con alta precisión.

## 🛠️ Estructura del Proyecto
- `main.py`: Interfaz gráfica (PyQt6) y manejo de hilos.
- `core/`: Motor de procesamiento y modelos de datos.
- `core/engine.py`: Integración con FFmpeg y Whisper.

## 🚀 Requisitos
- Python 3.9+
- FFmpeg instalado en el sistema.
- `pip install pyqt6 faster-whisper`