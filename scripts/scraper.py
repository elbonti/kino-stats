"""
01_actualizar.py
Módulo de Actualización: Consulta la API y agrega el último sorteo a la base maestra.
"""
import requests
import json
import os
from datetime import datetime

ARCHIVO_MAESTRO = "data/sorteos.json"
API_URL = "https://rckino.loteria.cl/api/sorteos"

VARIANTES = {0: "kino", 1: "reKino", 2: "requeteKino"}
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.loteria.cl/"
}

def obtener_ultimo_de_api():
    try:
        res = requests.get(API_URL, headers=HEADERS, timeout=15)
        res.raise_for_status()
        data = res.json()
        
        info = data.get("info", {})
        resumen = info.get("resumen", {})
        secciones = info.get("secciones", [])
        
        n_sorteo = int(resumen.get("numeroSorteo", 0))
        fecha = resumen.get("fechaSorteo", "").replace("/", "-")
        
        sorteo = {
            "numeroSorteo": n_sorteo,
            "fechaSorteo": fecha,
            "resultados": {v: {"numeros": [], "ganadores14": None, "pozoEstimado": None, "mensajeGanador": ""} for v in VARIANTES.values()}
        }
        
        for sec in secciones:
            cod = sec.get("codigoVariante")
            if cod not in VARIANTES: continue
            nombre = VARIANTES[cod]
            
            # Números
            bolitas = sec.get("bolitas", "")
            if bolitas:
                sorteo["resultados"][nombre]["numeros"] = sorted([int(b) for b in bolitas.split(",") if b.strip().isdigit()])
            
            # Pozo
            pozo_str = sec.get("pozoEstimado", "")
            if pozo_str:
                try: sorteo["resultados"][nombre]["pozoEstimado"] = int(pozo_str.replace(".","").replace(",",""))
                except: pass
            
            # Mensaje y Ganadores
            sorteo["resultados"][nombre]["mensajeGanador"] = sec.get("mensajeGanador", "")
            for cat in sec.get("categorias", []):
                if "14 Aciertos" in cat.get("nombreCategoria", ""):
                    try:
                        cant = cat.get("ganadores", {}).get("cantidad", "0")
                        sorteo["resultados"][nombre]["ganadores14"] = int(cant.replace(".","").replace(",",""))
                    except: pass
                    break
        return sorteo
    except Exception as e:
        print(f"❌ Error conectando a API: {e}")
        return None

def actualizar_base():
    print("🔄 Iniciando módulo de actualización...")
    
    # 1. Cargar base existente
    if os.path.exists(ARCHIVO_MAESTRO):
        with open(ARCHIVO_MAESTRO, 'r', encoding='utf-8') as f:
            data_maestra = json.load(f)
        sorteos = data_maestra.get("sorteos", [])
    else:
        print("⚠️ No existe sorteos.json. Se creará una base nueva.")
        data_maestra = {"sorteos": [], "metadata": {}}
        sorteos = []

    # 2. Obtener último de la API
    nuevo_sorteo = obtener_ultimo_de_api()
    if not nuevo_sorteo:
        print("❌ No se pudo obtener el sorteo de la API. Abortando.")
        return

    ultimo_api = nuevo_sorteo["numeroSorteo"]
    ultimo_local = sorteos[0]["numeroSorteo"] if sorteos else 0
    
    print(f"📊 Último en base: #{ultimo_local} | Último en API: #{ultimo_api}")

    # 3. Fusionar
    if ultimo_api > ultimo_local:
        print(f"✅ ¡Nuevo sorteo detectado! Agregando #{ultimo_api}...")
        sorteos.insert(0, nuevo_sorteo) # Insertar al principio (más reciente primero)
    elif ultimo_api == ultimo_local:
        print("🔄 Sorteo ya existe. Actualizando datos dinámicos (pozos/ganadores)...")
        for var in VARIANTES.values():
            sorteos[0]["resultados"][var].update(nuevo_sorteo["resultados"][var])
    else:
        print("⚠️ La API reporta un sorteo anterior. Verificar.")
        return

    # 4. Guardar
    data_maestra["sorteos"] = sorteos
    data_maestra["metadata"] = {
        "ultima_actualizacion": datetime.now().isoformat(),
        "total_sorteos": len(sorteos)
    }
    
    os.makedirs("data", exist_ok=True)
    with open(ARCHIVO_MAESTRO, 'w', encoding='utf-8') as f:
        json.dump(data_maestra, f, indent=2, ensure_ascii=False)
        
    print(f"💾 Base maestra actualizada y guardada en {ARCHIVO_MAESTRO}")

if __name__ == "__main__":
    actualizar_base()