import json
import pandas as pd
import os

ARCHIVO_HISTORIAL = "data/sorteos.json"
ARCHIVO_DASHBOARD = "data/dashboard_data.json"

# Definición de los Top 5 Grupos C
TOP_5_GRUPOS = {
    "C1": [3,6,7,8,10,11,12,14,15,16,18,22,23,24],
    "C17": [1,4,5,7,8,10,12,13,15,17,20,22,23,24],
    "C10": [1,2,4,5,7,8,10,11,13,14,16,17,20,23],
    "C3": [2,3,5,7,9,10,11,13,14,16,18,20,22,24],
    "C4": [1,3,4,6,8,10,12,14,16,18,20,22,24,25]
}

def procesar_datos():
    with open(ARCHIVO_HISTORIAL, "r", encoding="utf-8") as f:
        historial = json.load(f)
        
    df = pd.DataFrame(historial)
    total_sorteos = len(df)
    ultimo_sorteo = df.iloc[-1].to_dict()
    
    # --- MÓDULO B: Frecuencias ---
    # Expandimos la columna 'numeros' para contar frecuencias
    frecuencias = df['numeros'].explode().value_counts().sort_index()
    freq_data = [{"numero": i, "frecuencia": int(frecuencias.get(i, 0))} for i in range(1, 26)]
    
    # Calcular números calientes (top 5) y fríos (bottom 5)
    calientes = frecuencias.nlargest(5).index.tolist()
    frios = frecuencias.nsmallest(5).index.tolist()

    # --- MÓDULO C: Análisis de Grupos C ---
    analisis_grupos = {}
    ult_100 = df.tail(100)
    ult_500 = df.tail(500)
    
    for nombre, grupo in TOP_5_GRUPOS.items():
        set_grupo = set(grupo)
        
        # Aciertos últimos 100
        aciertos_100 = sum(len(set_grupo.intersection(set(numeros))) for numeros in ult_100['numeros'])
        
        # Máximo en últimos 500
        aciertos_500_list = [len(set_grupo.intersection(set(numeros))) for numeros in ult_500['numeros']]
        max_500 = max(aciertos_500_list) if aciertos_500_list else 0
        freq_max_500 = aciertos_500_list.count(max_500)
        
        analisis_grupos[nombre] = {
            "numeros": grupo,
            "aciertos_100": aciertos_100,
            "max_500": max_500,
            "freq_max_500": freq_max_500
        }

    # --- MÓDULO A y E: Resumen General ---
    dashboard_data = {
        "meta": {
            "total_sorteos": total_sorteos,
            "ultimo_sorteo": ultimo_sorteo,
            "actualizacion": pd.Timestamp.now().strftime("%d/%m/%Y %H:%M")
        },
        "modulo_b": {
            "frecuencias": freq_data,
            "calientes": calientes,
            "frios": frios
        },
        "modulo_c": analisis_grupos,
        "modulo_e": {
            "probabilidad_14": "1 en 3.268.700",
            "probabilidad_13": "1 en 214.391",
            "probabilidad_12": "1 en 10.209"
        }
    }

    os.makedirs("data", exist_ok=True)
    with open(ARCHIVO_DASHBOARD, "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=4, ensure_ascii=False)
    print("✅ Datos del dashboard generados en data/dashboard_data.json")

if __name__ == "__main__":
    procesar_datos()