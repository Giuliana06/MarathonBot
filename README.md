# MarathonBot - Taller de Programación II (UADE)

Este es un ChatBot de Telegram diseñado para planificar maratones de series de manera realista.
Calcula no solo la duración de los episodios, sino también los tiempos de pausa necesarios (snacks, baño, descanso), generando un gráfico visual del plan.

## Funcionalidades (MVP)
- **Búsqueda en tiempo real:** Conecta con la API de TMDB.
- **Cálculo Realista:** Agrega 10 minutos de pausa por episodio automáticamente.
- **Visualización:** Genera y envía un gráfico de torta (Pie Chart) con la distribución del tiempo.

## Requisitos
- Python 3.8 o superior.
- Una cuenta de Telegram.
- API Key de TMDB.

## Instalación y Uso

1. **Clonar el repositorio:**
   Descarga estos archivos en tu computadora.

2. **Instalar dependencias:**
   Ejecuta en la terminal:
   `pip install -r requirements.txt`

3. **Configuración:**
   Crea un archivo `config.py` (no incluido por seguridad) con tus claves:
   ```python
   TELEGRAM_TOKEN = "7950580345:AAEstqF-308yr3yTZ2q1GIsmrzhdTgg_uhM"
   TMDB_API_KEY = "244ed909392f316f9b9724b8845dfe3f"
   GEMINI_API_KEY = "AIzaSyDU3KgusT9NG0GdoClEPZ9w6Sog2j8bphA"
