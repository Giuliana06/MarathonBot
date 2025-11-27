import logging
import re
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import config
from data_fetcher import DataFetcher
from data_processor import DataProcessor
from api_gemini import preguntar_gemini

# Configuración de logs (para ver errores en la consola)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Instancias globales de los módulos
fetcher = DataFetcher()
processor = DataProcessor()

def limpiar_markdown(texto):
    """
    Limpia caracteres de Markdown que pueden causar errores en Telegram.
    Remueve asteriscos, guiones bajos y otros caracteres problemáticos.
    """
    # Remueve ** (negrita markdown)
    texto = re.sub(r'\*\*', '', texto)
    # Remueve * sueltos que no sean parte de listas
    texto = re.sub(r'(?<!\n)\*(?!\s)', '', texto)
    # Remueve __ (subrayado markdown)
    texto = re.sub(r'__', '', texto)
    # Remueve _ sueltos que podrían causar problemas
    texto = re.sub(r'(?<!\w)_(?!\w)', '', texto)
    # Remueve ``` bloques de código
    texto = re.sub(r'```[\s\S]*?```', '', texto)
    # Remueve ` inline code
    texto = re.sub(r'`', '', texto)
    return texto.strip()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="¡Hola! Soy MarathonBot 🎬.\nUsa /ayuda para ver qué puedo hacer."
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /ayuda"""
    mensaje = (
        "🤖 Comandos disponibles:\n\n"
        "🔹 /planear [título] - Calcula tiempo real de maratón y te ayuda a organizarte.\n"
        "🔹 /sinopsis [título] - Te cuento de qué trata la película o serie.\n"
        "🔹 /detalle [título] - Información técnica: duración, episodios, etc.\n"
        "🔹 /ayuda - Muestra este mensaje.\n"
        "\nEjemplo: /planear Breaking Bad"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)

async def _buscar_contenido(chat_id, context, args):
    """
    Función auxiliar para buscar contenido en TMDB.
    Retorna (resultado_busqueda, detalles) o (None, None) si falla.
    """
    if not args:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="⚠️ Por favor, escribe el nombre de la serie/película.\nEjemplo: /planear Titanic"
        )
        return None, None

    busqueda_usuario = ' '.join(args)
    await context.bot.send_message(chat_id=chat_id, text=f"🔍 Buscando '{busqueda_usuario}'...")

    resultado_busqueda = fetcher.buscar_titulo(busqueda_usuario)
    
    if not resultado_busqueda:
        await context.bot.send_message(
            chat_id=chat_id, 
            text="❌ No encontré nada con ese nombre. Intenta en inglés o revisa la ortografía."
        )
        return None, None

    detalles = fetcher.obtener_detalles(resultado_busqueda['id'], resultado_busqueda['media_type'])
    return resultado_busqueda, detalles

async def sinopsis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /sinopsis: Muestra la descripción de la película o serie.
    Usa Gemini para generar una respuesta atractiva.
    """
    chat_id = update.effective_chat.id
    
    resultado, detalles = await _buscar_contenido(chat_id, context, context.args)
    if not detalles:
        return

    # Preparamos los datos para Gemini
    instrucciones = """
    Eres un crítico de cine y series amigable y entusiasta. 
    Tu tarea es presentar la sinopsis de una película o serie de forma atractiva y enganchante.
    Usa emojis apropiados. Sé conciso pero interesante. 
    No reveles spoilers importantes. Genera entusiasmo por ver el contenido.
    Responde en español. Máximo 200 palabras.
    IMPORTANTE: No uses formato Markdown (nada de asteriscos, guiones bajos, etc). Solo texto plano con emojis.
    """
    
    tipo_contenido = "serie" if detalles['tipo'] == 'tv' else "película"
    pregunta = f"""
    Presenta la sinopsis de esta {tipo_contenido}:
    
    Título: {detalles['titulo']}
    Tipo: {tipo_contenido}
    Sinopsis original: {detalles['sinopsis']}
    """
    
    try:
        respuesta_gemini = limpiar_markdown(preguntar_gemini(pregunta, instrucciones))
        mensaje = f"🎬 {detalles['titulo']}\n\n{respuesta_gemini}"
    except Exception as e:
        logging.error(f"Error con Gemini: {e}")
        mensaje = f"🎬 {detalles['titulo']}\n\n📝 {detalles['sinopsis']}"
    
    await context.bot.send_message(chat_id=chat_id, text=mensaje)

async def detalle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /detalle: Muestra información técnica (duración, episodios, etc.)
    Usa Gemini para generar una respuesta informativa.
    """
    chat_id = update.effective_chat.id
    
    resultado, detalles = await _buscar_contenido(chat_id, context, context.args)
    if not detalles:
        return

    # Preparamos los datos para Gemini
    instrucciones = """
    Eres un asistente informativo sobre películas y series.
    Tu tarea es presentar los datos técnicos de forma clara y organizada.
    Usa emojis apropiados para cada dato. Sé preciso y conciso.
    Responde en español. Formato tipo ficha técnica.
    IMPORTANTE: No uses formato Markdown (nada de asteriscos, guiones bajos, etc). Solo texto plano con emojis.
    """
    
    tipo_contenido = "serie" if detalles['tipo'] == 'tv' else "película"
    
    if tipo_contenido == "serie":
        pregunta = f"""
        Presenta la ficha técnica de esta serie:
        
        Título: {detalles['titulo']}
        Tipo: Serie de TV
        Cantidad de episodios: {detalles['cantidad_episodios']}
        Duración promedio por episodio: {detalles['duracion_minutos']} minutos
        Duración total aproximada: {detalles['duracion_minutos'] * detalles['cantidad_episodios']} minutos
        """
    else:
        pregunta = f"""
        Presenta la ficha técnica de esta película:
        
        Título: {detalles['titulo']}
        Tipo: Película
        Duración: {detalles['duracion_minutos']} minutos
        """
    
    try:
        respuesta_gemini = limpiar_markdown(preguntar_gemini(pregunta, instrucciones))
        mensaje = f"📊 Ficha Técnica: {detalles['titulo']}\n\n{respuesta_gemini}"
    except Exception as e:
        logging.error(f"Error con Gemini: {e}")
        # Fallback sin Gemini
        if tipo_contenido == "serie":
            mensaje = (
                f"📊 Ficha Técnica: {detalles['titulo']}\n\n"
                f"📺 Tipo: Serie\n"
                f"🎬 Episodios: {detalles['cantidad_episodios']}\n"
                f"⏱ Duración por episodio: {detalles['duracion_minutos']} min\n"
                f"⏳ Duración total: {detalles['duracion_minutos'] * detalles['cantidad_episodios']} min"
            )
        else:
            mensaje = (
                f"📊 Ficha Técnica: {detalles['titulo']}\n\n"
                f"🎥 Tipo: Película\n"
                f"⏱ Duración: {detalles['duracion_minutos']} min"
            )
    
    await context.bot.send_message(chat_id=chat_id, text=mensaje)

async def planear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /planear: Calcula tiempo real de maratón y ayuda a organizarse.
    Usa Gemini para generar consejos personalizados.
    """
    chat_id = update.effective_chat.id
    
    resultado, detalles = await _buscar_contenido(chat_id, context, context.args)
    if not detalles:
        return

    # Calcular el plan realista usando DataProcessor
    plan = processor.calcular_plan_realista(
        duracion_minutos=detalles['duracion_minutos'],
        cantidad_episodios=detalles['cantidad_episodios']
    )

    # Generar el gráfico
    ruta_grafico = processor.generar_grafico_torta(plan, detalles['titulo'])

    # Preparamos los datos para Gemini
    instrucciones = """
    Eres un experto planificador de maratones de películas y series.
    Tu tarea es ayudar al usuario a organizar su maratón de forma realista y divertida.
    Da consejos prácticos sobre pausas, snacks, comodidad, etc.
    Usa emojis apropiados. Sé motivador y amigable.
    Responde en español. Máximo 250 palabras.
    Incluye los datos de tiempo que te proporciono de forma natural en tu respuesta.
    IMPORTANTE: No uses formato Markdown (nada de asteriscos, guiones bajos, etc). Solo texto plano con emojis.
    """
    
    tipo_contenido = "serie" if detalles['tipo'] == 'tv' else "película"
    
    pregunta = f"""
    Ayuda a planificar un maratón para ver esta {tipo_contenido}:
    
    Título: {detalles['titulo']}
    Tipo: {tipo_contenido}
    Episodios/películas: {detalles['cantidad_episodios']}
    Duración por unidad: {detalles['duracion_minutos']} minutos
    
    Datos calculados del maratón:
    - Tiempo total en pantalla: {plan['tiempo_pantalla']} minutos
    - Tiempo estimado de pausas (baño, comida, estirar): {plan['tiempo_pausas']} minutos
    - TIEMPO TOTAL REAL NECESARIO: {plan['horas_totales']} horas ({plan['tiempo_total']} minutos)
    
    Genera un plan de maratón con consejos prácticos para disfrutarlo al máximo.
    """
    
    try:
        respuesta_gemini = limpiar_markdown(preguntar_gemini(pregunta, instrucciones))
        mensaje = f"🎬 Plan de Maratón: {detalles['titulo']}\n\n{respuesta_gemini}"
    except Exception as e:
        logging.error(f"Error con Gemini: {e}")
        # Fallback sin Gemini (respuesta original)
        mensaje = (
            f"🎬 Plan de Maratón: {detalles['titulo']}\n\n"
            f"⏱ Datos del Maratón:\n"
            f"- Tiempo en pantalla: {plan['tiempo_pantalla']} min\n"
            f"- Tiempo de pausas: {plan['tiempo_pausas']} min\n"
            f"----------------------------------\n"
            f"🏆 TIEMPO TOTAL REAL: {plan['horas_totales']} HORAS"
        )

    # Enviar mensaje y gráfico
    await context.bot.send_message(chat_id=chat_id, text=mensaje)
    await context.bot.send_photo(chat_id=chat_id, photo=open(ruta_grafico, 'rb'))

if __name__ == '__main__':
    # Iniciamos la aplicación con el Token de config.py
    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    
    # Conectamos los comandos a las funciones
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ayuda', ayuda))
    application.add_handler(CommandHandler('planear', planear))
    application.add_handler(CommandHandler('sinopsis', sinopsis))
    application.add_handler(CommandHandler('detalle', detalle))
    
    print("🤖 MarathonBot está escuchando...")
    application.run_polling()

