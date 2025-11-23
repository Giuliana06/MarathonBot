#cálculos de tiempo y gráficos

import matplotlib.pyplot as plt
import os

class DataProcessor:
    """
    Clase encargada de la lógica de negocio y visualización.
    Corresponde al 'Módulo de Procesamiento' del TP.
    """

    def __init__(self):
        # Definimos una pausa estándar de 10 minutos por episodio/película
        self.pausa_por_unidad = 10 

    def calcular_plan_realista(self, duracion_minutos, cantidad_episodios):
        """
        Transforma la duración bruta en un plan realista.
        Formula: (Duración * Episodios) + (Pausa * Episodios)
        """
        tiempo_pantalla = duracion_minutos * cantidad_episodios
        tiempo_pausas = self.pausa_por_unidad * cantidad_episodios
        tiempo_total = tiempo_pantalla + tiempo_pausas
        
        return {
            "tiempo_pantalla": tiempo_pantalla,
            "tiempo_pausas": tiempo_pausas,
            "tiempo_total": tiempo_total,
            "horas_totales": round(tiempo_total / 60, 1) # Convertimos a horas con 1 decimal
        }

    def generar_grafico_torta(self, datos_plan, titulo):
        """
        Genera un gráfico de pastel (Pie Chart) usando Matplotlib.
        Guarda la imagen en disco para que el bot pueda enviarla.
        """
        # Datos para el gráfico
        etiquetas = ['Tiempo Viendo', 'Tiempo de Pausa']
        valores = [datos_plan['tiempo_pantalla'], datos_plan['tiempo_pausas']]
        colores = ['#3498db', '#95a5a6'] # Azul y Gris

        # Crear la figura
        plt.figure(figsize=(6, 4))
        plt.pie(valores, labels=etiquetas, colors=colores, autopct='%1.1f%%', startangle=90)
        plt.title(f"Distribución de tiempo para:\n{titulo}")
        
        # Guardar la imagen
        nombre_archivo = "grafico_temporal.png"
        plt.savefig(nombre_archivo)
        plt.close() # Cerramos para liberar memoria
        
        return nombre_archivo

# --- ZONA DE PRUEBA (Para verificar que el gráfico se crea bien) ---
if __name__ == "__main__":
    procesador = DataProcessor()
    
    # Simulamos una serie de 10 episodios de 50 minutos
    print("Calculando plan para una serie de prueba...")
    plan = procesador.calcular_plan_realista(duracion_minutos=50, cantidad_episodios=10)
    
    print(f"Cálculo completado: {plan['horas_totales']} horas totales.")
    
    print("Generando gráfico...")
    archivo = procesador.generar_grafico_torta(plan, "Serie de Prueba")
    print(f"Gráfico generado exitosamente: {archivo}")
    print("¡Revisa la carpeta de tu proyecto, deberías ver una imagen nueva!")