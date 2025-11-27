import google.generativeai as genai
import config

genai.configure(api_key=config.GEMINI_API_KEY)

def crear_modelo(instrucciones):
    model = genai.GenerativeModel(model_name='gemini-2.5-flash', system_instruction=instrucciones)
    return model

def preguntar_gemini(pregunta, instrucciones=None):
    model = crear_modelo(instrucciones)
    response = model.generate_content(pregunta)
    return response.text
