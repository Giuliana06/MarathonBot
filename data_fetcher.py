#conexión con TMDB

import requests
import config # Importamos las claves de nuestro archivo config

class DataFetcher:
    """
    Clase encargada de la comunicación con la API de TMDB.
    Corresponde al 'Módulo de Extracción' del TP.
    """
    
    def __init__(self):
        self.api_key = config.TMDB_API_KEY
        self.base_url = "https://api.themoviedb.org/3"

    def buscar_titulo(self, query):
        """
        Busca una película o serie por nombre.
        Retorna el primer resultado encontrado o None si no hay nada.
        """
        # Usamos el endpoint 'search/multi' para buscar pelis y series a la vez
        url = f"{self.base_url}/search/multi"
        params = {
            "api_key": self.api_key,
            "query": query,
            "language": "es-ES" # Pedimos los datos en español
        }
        
        try:
            respuesta = requests.get(url, params=params)
            respuesta.raise_for_status() # Avisa si hubo error de conexión
            datos = respuesta.json()
            
            if datos['results']:
                # Devolvemos solo el primer resultado (el más relevante)
                return datos['results'][0]
            else:
                return None
        except Exception as e:
            print(f"Error buscando titulo: {e}")
            return None

    def obtener_detalles(self, tmdb_id, media_type):
        """
        Obtiene la duración exacta.
        Si es película: busca 'runtime'.
        Si es serie: busca duración promedio de episodios y cantidad de epis.
        """
        url = f"{self.base_url}/{media_type}/{tmdb_id}"
        params = {
            "api_key": self.api_key,
            "language": "es-ES"
        }
        
        try:
            respuesta = requests.get(url, params=params)
            datos = respuesta.json()
            
            # Estandarizamos la respuesta para que sea fácil de usar después
            resultado = {
                "titulo": datos.get("title") or datos.get("name"),
                "tipo": media_type,
                "sinopsis": datos.get("overview", "Sin descripción disponible."),
                "duracion_minutos": 0,
                "cantidad_episodios": 1 # Por defecto 1 (para películas)
            }

            if media_type == 'movie':
                resultado["duracion_minutos"] = datos.get("runtime", 0)
            
            elif media_type == 'tv':
                # Las series a veces tienen varios tiempos, tomamos el primero si existe
                tiempos = datos.get("episode_run_time", [])
                if tiempos:
                    promedio = sum(tiempos) / len(tiempos)
                    resultado["duracion_minutos"] = int(promedio)
                else:
                    # A veces TMDB no tiene el tiempo exacto, estimamos 45 min
                    resultado["duracion_minutos"] = 45 
                
                resultado["cantidad_episodios"] = datos.get("number_of_episodes", 0)
                
            return resultado

        except Exception as e:
            print(f"Error obteniendo detalles: {e}")
            return None

# --- ZONA DE PRUEBA (Solo corre si ejecutamos este archivo directamente) ---
if __name__ == "__main__":
    # Esto es para probar si funciona sin prender el bot entero
    buscador = DataFetcher()
    print("Probando buscador con 'Breaking Bad'...")
    encontrado = buscador.buscar_titulo("Breaking Bad")
    
    if encontrado:
        print(f"Encontré: {encontrado.get('name') or encontrado.get('title')} (ID: {encontrado['id']})")
        detalles = buscador.obtener_detalles(encontrado['id'], encontrado['media_type'])
        print("Detalles finales extraídos:", detalles)
    else:
        print("No se encontró nada.")