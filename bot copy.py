import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import config
from data_fetcher import DataFetcher
from data_processor import DataProcessor

# --- CONFIGURACIÓN DE CLAVES ---
# Configuramos la clave de Gemini en el entorno para que AIAnalyzer la encuentre.
# (Usando la clave que estaba en tu archivo api_gemini.py)
os.environ["GEMINI_API_KEY"] = "AIzaSyDU3KgusT9NG0GdoClEPZ9w6Sog2j8bphA"

# Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=(
            "¡Hola! Soy MarathonBot 🎬.\n"
            "Te ayudo a organizar tus maratones de series y películas.\n"
            "Usa /ayuda para ver los comandos."
        )
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /ayuda"""
    mensaje = (
        "🤖 **Comandos disponibles:**\n\n"
        "🔹 /planear [título] \n   -> Calcula tiempo total y genera gráfico.\n"
        "🔹 /ajustar [título], [minutos] \n   -> Te dice cuánto ver según tu tiempo libre.\n"
        "🔹 /analisis [título] \n   -> Usa IA para analizar el tono y temas.\n"
        "🔹 /ayuda \n   -> Muestra este mensaje.\n"
        "\nEjemplos:\n"
        "/planear Breaking Bad\n"
        "/ajustar Titanic, 120\n"
        "/analisis The Office"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)

async def planear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /planear: Busca, calcula maratón y envía gráfico.
    """
    chat_id = update.effective_chat.id
    
    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Escribe el nombre de la serie/película. Ej: /planear Matrix")
        return

    titulo_busqueda = ' '.join(context.args)
    await context.bot.send_message(chat_id=chat_id, text=f"🔍 Buscando '{titulo_busqueda}'...")

    try:
        # 1. Instanciar Fetcher con la clave de config.py
        fetcher = DataFetcher(config.TMDB_KEY)
        
        # 2. Obtener datos limpios
        datos = fetcher.get_details(titulo_busqueda)
        
        # 3. Calcular Maratón (Processor)
        plan = DataProcessor.calcular_maraton(datos)
        
        # 4. Generar Gráfico (Processor)
        ruta_grafico = DataProcessor.generar_grafico(plan)

        # 5. Armar mensaje
        mensaje = (
            f"🎬 **Plan: {plan['title']}**\n"
            f"📦 Unidades (eps/peli): {plan['unidades']}\n"
            f"👀 Tiempo visualización: {plan['ver_min']} min\n"
            f"☕ Tiempo pausas: {plan['pausa_min']} min\n"
            f"----------------------------------\n"
            f"⏱ **DURACIÓN TOTAL:** {plan['formato_final']}"
        )

        # Enviar texto e imagen
        await context.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')
        await context.bot.send_photo(chat_id=chat_id, photo=open(ruta_grafico, 'rb'))

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")

async def ajustar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /ajustar: Calcula cuánto ver dado un límite de tiempo.
    Formato esperado: /ajustar Titulo, Minutos
    """
    chat_id = update.effective_chat.id
    args_texto = ' '.join(context.args)
    
    # Separar por coma
    if "," not in args_texto:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Formato incorrecto. Usa: /ajustar Titulo, Minutos\nEj: /ajustar Friends, 60")
        return

    try:
        titulo, minutos_str = args_texto.rsplit(',', 1)
        tiempo_disponible = int(minutos_str.strip())
        
        # 1. Buscar datos
        fetcher = DataFetcher(config.TMDB_KEY)
        datos = fetcher.get_details(titulo.strip())
        
        # 2. Calcular ajuste
        ajuste = DataProcessor.ajustar_sesion(datos, tiempo_disponible)
        
        mensaje = (
            f"⚖️ **Sesión Ajustada: {ajuste['title']}**\n"
            f"⏳ Tienes: {tiempo_disponible} min\n\n"
            f"📺 **Debes ver:** {ajuste['ver_min']} min de contenido\n"
            f"⏸ **Pausas:** {ajuste['pausa_min']} min\n"
            f"---------------------------\n"
            f"📝 {ajuste['resumen']}"
        )
        if "episodios" in ajuste:
            mensaje += f"\n(Son {ajuste['episodios']} episodios completos)"

        await context.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')

    except ValueError:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Los minutos deben ser un número.")
    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error: {str(e)}")

async def analisis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /analisis: Usa Gemini para analizar la sinopsis.
    """
    chat_id = update.effective_chat.id
    
    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Escribe el título. Ej: /analisis Inception")
        return

    titulo = ' '.join(context.args)
    await context.bot.send_message(chat_id=chat_id, text=f"🤖 Consultando a la IA sobre '{titulo}'...")

    try:
        fetcher = DataFetcher(config.TMDB_KEY)
        datos = fetcher.get_details(titulo)
        
        # Llamada al Processor -> AIAnalyzer
        resultado_ia = DataProcessor.run_content_analysis(datos)
        
        mensaje = (
            f"🧠 **Análisis de IA: {datos['title']}**\n\n"
            f"{resultado_ia}"
        )
        await context.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode='Markdown')

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ Error en análisis: {str(e)}")


if __name__ == '__main__':
    # IMPORTANTE: Asegúrate de que TELEGRAM_TOKEN esté en config.py
    if not hasattr(config, 'TELEGRAM_TOKEN'):
        print("❌ ERROR: Falta TELEGRAM_TOKEN en config.py")
    else:
        application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(CommandHandler('ayuda', ayuda))
        application.add_handler(CommandHandler('planear', planear))
        application.add_handler(CommandHandler('ajustar', ajustar))
        application.add_handler(CommandHandler('analisis', analisis))
        
        print("🤖 MarathonBot Pro iniciado y listo...")
        application.run_polling() 