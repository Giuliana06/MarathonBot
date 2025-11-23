import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import config
from data_fetcher import DataFetcher
from data_processor import DataProcessor

# Configuración de logs (para ver errores en la consola)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /start"""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="¡Hola! Soy MarathonBot 🎬.\nUsa /ayuda para ver qué puedo hacer."
    )

async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Responde al comando /ayuda [cite: 39]"""
    mensaje = (
        "🤖 **Comandos disponibles:**\n\n"
        "🔹 /planear [título] - Calcula tiempo real de maratón + gráfico.\n"
        "🔹 /ayuda - Muestra este mensaje.\n"
        "\nEjemplo: /planear Breaking Bad"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=mensaje)

async def planear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando principal del MVP (/planear).
    Orquesta la búsqueda, cálculo y respuesta visual[cite: 32].
    """
    chat_id = update.effective_chat.id
    
    # 1. Validar que el usuario escribió un título
    if not context.args:
        await context.bot.send_message(chat_id=chat_id, text="⚠️ Por favor, escribe el nombre de la serie/película.\nEjemplo: /planear Titanic")
        return

    # Unimos las palabras del título (ej: "Breaking", "Bad" -> "Breaking Bad")
    busqueda_usuario = ' '.join(context.args)
    await context.bot.send_message(chat_id=chat_id, text=f"🔍 Buscando '{busqueda_usuario}' en la base de datos...")

    # 2. Instanciar nuestros módulos (POO) [cite: 14]
    fetcher = DataFetcher()
    processor = DataProcessor()

    # 3. Buscar datos (DataFetcher) [cite: 19]
    resultado_busqueda = fetcher.buscar_titulo(busqueda_usuario)
    
    if not resultado_busqueda:
        await context.bot.send_message(chat_id=chat_id, text="❌ No encontré nada con ese nombre. Intenta en inglés o revisa la ortografía.")
        return

    # Obtener detalles técnicos (duración, episodios)
    detalles = fetcher.obtener_detalles(resultado_busqueda['id'], resultado_busqueda['media_type'])
    
    # 4. Procesar datos y Calcular Plan (DataProcessor) [cite: 22]
    plan = processor.calcular_plan_realista(
        duracion_minutos=detalles['duracion_minutos'],
        cantidad_episodios=detalles['cantidad_episodios']
    )

    # 5. Generar Gráfico (Visualización) [cite: 26]
    ruta_grafico = processor.generar_grafico_torta(plan, detalles['titulo'])

    # 6. Armar respuesta de texto (Reporte) [cite: 27]
    mensaje_final = (
        f"🎬 **Plan de Maratón: {detalles['titulo']}**\n"
        f"📝 *Sinopsis*: {detalles['sinopsis'][:150]}...\n\n"
        f"⏱ **Datos Técnicos**:\n"
        f"- Episodios: {detalles['cantidad_episodios']}\n"
        f"- Duración unitaria: {detalles['duracion_minutos']} min\n\n"
        f"📊 **Análisis Realista (MVP)**:\n"
        f"- Tiempo en pantalla: {plan['tiempo_pantalla']} min\n"
        f"- Tiempo de pausas (baño/comida): {plan['tiempo_pausas']} min\n"
        f"----------------------------------\n"
        f"🏆 **TIEMPO TOTAL REAL: {plan['horas_totales']} HORAS**"
    )

    # 7. Enviar respuesta + Foto [cite: 28]
    await context.bot.send_message(chat_id=chat_id, text=mensaje_final, parse_mode='Markdown')
    
    # Enviamos la imagen del gráfico
    await context.bot.send_photo(chat_id=chat_id, photo=open(ruta_grafico, 'rb'))

if __name__ == '__main__':
    # Iniciamos la aplicación con el Token de config.py
    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()
    
    # Conectamos los comandos a las funciones
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('ayuda', ayuda))
    application.add_handler(CommandHandler('planear', planear))
    
    print("🤖 MarathonBot está escuchando...")
    application.run_polling()
    
