import json
import pandas as pd
import os

def procesar_datos():
    # Cargar datos con manejo de errores
    try:
        with open("data/historial.json", "r", encoding="utf-8") as f:
            historial = json.load(f)
    except FileNotFoundError:
        print("❌ Error: No se encontró data/historial.json")
        print("   Ejecuta primero el scraper: python scripts/scraper.py")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Error: El archivo JSON está mal formado: {e}")
        return
    
    if not historial:
        print("❌ Error: El archivo historial.json está vacío")
        return
    
    # Normalizar datos: asegurar que todos los sorteos tengan la misma estructura
    sorteos_normalizados = []
    for i, sorteo in enumerate(historial):
        try:
            # Validar campos requeridos
            if "sorteo" not in sorteo or "fecha" not in sorteo or "numeros" not in sorteo:
                print(f"⚠️  Sorteo {i} incompleto, saltando: {sorteo}")
                continue
            
            # Normalizar números (puede venir como string o lista)
            numeros = sorteo["numeros"]
            if isinstance(numeros, str):
                # Si es string, convertir a lista de enteros
                numeros = [int(n.strip()) for n in numeros.split(",") if n.strip().isdigit()]
            elif isinstance(numeros, list):
                # Si es lista, asegurar que sean enteros
                numeros = [int(n) for n in numeros if str(n).isdigit()]
            else:
                print(f"⚠️  Sorteo {i} tiene formato de números inválido: {type(numeros)}")
                continue
            
            # Validar que tenga 14 o 15 números
            if len(numeros) not in [14, 15]:
                print(f"⚠️  Sorteo {i} tiene {len(numeros)} números (esperado 14 o 15)")
                continue
            
            sorteos_normalizados.append({
                "sorteo": sorteo["sorteo"],
                "fecha": sorteo["fecha"],
                "numeros": numeros
            })
        except Exception as e:
            print(f"⚠️  Error procesando sorteo {i}: {e}")
            continue
    
    if not sorteos_normalizados:
        print("❌ Error: No hay sorteos válidos después de la normalización")
        return
    
    print(f"✅ {len(sorteos_normalizados)} sorteos normalizados correctamente")
    
    # Crear DataFrame
    df = pd.DataFrame(sorteos_normalizados)
    
    # Ordenar por número de sorteo
    df = df.sort_values("sorteo").reset_index(drop=True)
    
    # Calcular estadísticas
    total_sorteos = len(df)
    ultimo_sorteo = df.iloc[-1].to_dict()
    
    # Frecuencias históricas
    frecuencias = df['numeros'].explode().value_counts().sort_index()
    freq_data = [{"numero": i, "frecuencia": int(frecuencias.get(i, 0))} for i in range(1, 26)]
    
    # Calientes y fríos
    calientes = frecuencias.nlargest(5).index.tolist()
    frios = frecuencias.nsmallest(5).index.tolist()
    
    # Definir grupos (ajusta según tus grupos reales)
    TOP_5_GRUPOS = {
        "C1": [3,6,7,8,10,11,12,14,15,16,18,22,23,24],
        "C17": [1,4,5,7,8,10,12,13,15,17,20,22,23,24],
        "C10": [1,2,4,5,7,8,10,11,13,14,16,17,20,23],
        "C3": [2,3,5,7,9,10,11,13,14,16,18,20,22,24],
        "C4": [1,3,4,6,8,10,12,14,16,18,20,22,24,25]
    }
    
    # Calcular métricas para cada grupo
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
    
    # Generar JSON final
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
    
    # Guardar en frontend
    os.makedirs("frontend", exist_ok=True)
    with open("frontend/datos.json", "w", encoding="utf-8") as f:
        json.dump(dashboard_data, f, indent=4, ensure_ascii=False)
    
    print("✅ Dashboard data generado en frontend/datos.json")

if __name__ == "__main__":
    procesar_datos()