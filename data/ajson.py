import pandas as pd
import requests
import json
import time
import os
from datetime import datetime

# --- CONFIGURACIÓN ---
ARCHIVO_EXCEL = "data/base_k.xlsx"
ARCHIVO_SALIDA = "data/sorteos.json"
API_BASE_URL = "https://rckino.loteria.cl/api/sorteos"

VARIANTES = {
    0: "kino",
    1: "reKino",
    2: "requeteKino"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.loteria.cl/",
    "Origin": "https://www.loteria.cl"
}

def leer_hoja_excel(nombre_hoja, num_numeros):
    """Lee una hoja del Excel y extrae sorteo, fecha, números y ganadores."""
    df = pd.read_excel(ARCHIVO_EXCEL, sheet_name=nombre_hoja)
    datos = {}
    for _, row in df.iterrows():
        if pd.isna(row.iloc[0]): continue
        try:
            n_sorteo = int(row.iloc[0])
            fecha = str(row.iloc[1]).split()[0]
            # Asumimos que la última columna de la hoja es la de ganadores
            ganadores = int(row.iloc[-1]) if pd.notna(row.iloc[-1]) else 0
            # Los números están desde la columna 2 (índice 2) hasta 2 + num_numeros
            numeros = []
            for i in range(2, 2 + num_numeros):
                if i < len(row) and pd.notna(row.iloc[i]):
                    try:
                        numeros.append(int(float(row.iloc[i])))
                    except:
                        pass
            datos[n_sorteo] = {
                "fecha": fecha,
                "numeros": sorted(list(set(numeros))),
                "ganadores14": ganadores
            }
        except:
            continue
    return datos

def leer_excel_completo():
    """Lee las tres hojas del Excel y unifica los datos por sorteo."""
    print("📊 Leyendo archivo Excel completo...")
    
    kino_data = leer_hoja_excel("Kino", 15)
    rekino_data = leer_hoja_excel("Rekino", 14)
    requetekino_data = leer_hoja_excel("Requetekino", 14)
    
    todos_sorteos = set(kino_data.keys()) | set(rekino_data.keys()) | set(requetekino_data.keys())
    
    sorteos_base = []
    for n_sorteo in sorted(todos_sorteos):
        sorteo = {
            "numeroSorteo": n_sorteo,
            "fechaSorteo": "",
            "resultados": {
                "kino": {"numeros": [], "ganadores14": 0, "pozoEstimado": None, "mensajeGanador": None},
                "reKino": {"numeros": [], "ganadores14": 0, "pozoEstimado": None, "mensajeGanador": None},
                "requeteKino": {"numeros": [], "ganadores14": 0, "pozoEstimado": None, "mensajeGanador": None}
            }
        }
        
        if n_sorteo in kino_data:
            sorteo["fechaSorteo"] = kino_data[n_sorteo]["fecha"]
            sorteo["resultados"]["kino"]["numeros"] = kino_data[n_sorteo]["numeros"]
            sorteo["resultados"]["kino"]["ganadores14"] = kino_data[n_sorteo]["ganadores14"]
            
        if n_sorteo in rekino_data:
            sorteo["resultados"]["reKino"]["numeros"] = rekino_data[n_sorteo]["numeros"]
            sorteo["resultados"]["reKino"]["ganadores14"] = rekino_data[n_sorteo]["ganadores14"]
            
        if n_sorteo in requetekino_data:
            sorteo["resultados"]["requeteKino"]["numeros"] = requetekino_data[n_sorteo]["numeros"]
            sorteo["resultados"]["requeteKino"]["ganadores14"] = requetekino_data[n_sorteo]["ganadores14"]
            
        sorteos_base.append(sorteo)
        
    print(f"✅ Se leyeron {len(sorteos_base)} sorteos del Excel.")
    return sorteos_base

def consultar_api_sorteo(numero_sorteo):
    """Consulta la API para un sorteo específico."""
    url = f"{API_BASE_URL}?sorteo={numero_sorteo}"
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        secciones = data.get("info", {}).get("secciones", [])
        datos_sorteo = {}
        
        for seccion in secciones:
            codigo = seccion.get("codigoVariante")
            if codigo not in VARIANTES:
                continue
                
            nombre = VARIANTES[codigo]
            
            pozo_str = seccion.get("pozoEstimado", "")
            pozo = None
            if pozo_str:
                try:
                    pozo = int(pozo_str.replace(".", "").replace(",", ""))
                except:
                    pozo = None
                    
            mensaje = seccion.get("mensajeGanador", "")
            
            datos_sorteo[nombre] = {
                "pozoEstimado": pozo,
                "mensajeGanador": mensaje
            }
            
        return datos_sorteo
        
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️ Error de red en sorteo {numero_sorteo}: {e}")
        return None
    except Exception as e:
        print(f"  ⚠️ Error procesando sorteo {numero_sorteo}: {e}")
        return None

def fusionar_y_generar_json(sorteos_base):
    """Fusiona los datos del Excel con las consultas a la API."""
    max_sorteo = max(s["numeroSorteo"] for s in sorteos_base)
    sorteos_a_consultar = list(range(max(max_sorteo - 25, 0), max_sorteo + 1))
    
    print(f"\n🌐 Consultando API para los últimos {len(sorteos_a_consultar)} sorteos (del {sorteos_a_consultar[0]} al {max_sorteo})...")
    print(f"   Pausa entre llamadas: 2.5 segundos")
    print("-" * 60)
    
    api_data = {}
    total = len(sorteos_a_consultar)
    
    for i, num_sorteo in enumerate(sorteos_a_consultar, 1):
        print(f"[{i}/{total}] Consultando sorteo {num_sorteo}...", end=" ")
        datos = consultar_api_sorteo(num_sorteo)
        
        if datos:
            api_data[num_sorteo] = datos
            print("✅ OK")
        else:
            print("❌ Falló")
            
        if i < total:
            time.sleep(2.5)
            
    print("-" * 60)
    print(f"✅ Consulta completada: {len(api_data)}/{total} sorteos obtenidos")
    
    print("\n🔄 Fusionando datos...")
    sorteos_finales = []
    sorteos_con_pozos_count = 0
    
    for sorteo in sorteos_base:
        num = sorteo["numeroSorteo"]
        
        if num in api_data:
            tiene_pozo = False
            for variante in ["kino", "reKino", "requeteKino"]:
                if variante in api_data[num]:
                    datos_api = api_data[num][variante]
                    sorteo["resultados"][variante]["pozoEstimado"] = datos_api["pozoEstimado"]
                    sorteo["resultados"][variante]["mensajeGanador"] = datos_api["mensajeGanador"]
                    
                    if datos_api["pozoEstimado"] is not None:
                        tiene_pozo = True
            
            if tiene_pozo:
                sorteos_con_pozos_count += 1
                
        sorteos_finales.append(sorteo)
        
    sorteos_finales.sort(key=lambda x: x["numeroSorteo"], reverse=True)
    
    output = {
        "metadata": {
            "ultima_actualizacion": datetime.now().isoformat(),
            "total_sorteos": len(sorteos_finales),
            "sorteos_con_pozos": sorteos_con_pozos_count,
            "fuente_historial": "base_k.xlsx",
            "fuente_pozos": "rckino.loteria.cl/api/sorteos"
        },
        "sorteos": sorteos_finales
    }
    
    print(f"\n💾 Guardando archivo {ARCHIVO_SALIDA}...")
    with open(ARCHIVO_SALIDA, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        
    print("✅ ¡Proceso completado exitosamente!")
    print(f"   - Total de sorteos en JSON: {len(sorteos_finales)}")
    print(f"   - Sorteos con datos de pozos actualizados: {sorteos_con_pozos_count}")

if __name__ == "__main__":
    if not os.path.exists(ARCHIVO_EXCEL):
        print(f"❌ Error: No se encuentra el archivo '{ARCHIVO_EXCEL}'.")
        print("   Asegúrate de que esté en la misma carpeta que este script.")
    else:
        print("=" * 60)
        print("🎰 ACTUALIZACIÓN DE DATOS KINO")
        print("=" * 60)
        base = leer_excel_completo()
        fusionar_y_generar_json(base)
        print("\n" + "=" * 60)
        print("✅ PROCESO COMPLETADO")
        print("=" * 60)