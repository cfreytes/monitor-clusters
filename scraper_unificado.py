import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
HOY = datetime.today().strftime("%Y-%m-%d")

# ─────────────────────────────────────────────
# FUENTE 1: ProCórdoba  — FIX: busca div.card-event-body
# ─────────────────────────────────────────────
def scrape_procordoba():
    URL_BASE = "https://procordoba.org/calendario/"
    resultados = []

    def scrapear_pagina(pagina_num):
        url = URL_BASE if pagina_num == 1 else f"{URL_BASE}?pg={pagina_num}"
        response = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        eventos = []

        for titulo in soup.find_all("h5", class_="card-title"):
            nombre = titulo.get_text(strip=True)
            if not nombre:
                continue

            # FIX: sube al contenedor correcto (card-event-body)
            bloque = titulo.find_parent("div", class_="card-event-body")
            if not bloque:
                continue

            partes = [p.strip() for p in bloque.get_text(separator=" | ", strip=True).split("|")]

            # Fecha: parte que contiene "/" y tiene largo corto
            fecha = next(
                (p.strip().replace("📅","").strip()
                 for p in partes if "/" in p and len(p.strip()) < 35 and p.strip() != nombre),
                ""
            )

            # Estado: parte que contiene "📌"
            estado = next(
                (p.strip().replace("📌","").strip() for p in partes if "📌" in p),
                ""
            )

            # Sectores: links con ?sector=
            sectores = [a.get_text(strip=True) for a in bloque.find_all("a", href=True)
                        if "sector=" in a.get("href","")]

            # Destino: links con ?pais=
            paises = [a.get_text(strip=True) for a in bloque.find_all("a", href=True)
                      if "pais=" in a.get("href","")]

            eventos.append({
                "titulo":        nombre,
                "tipo":          "Misión Comercial",
                "sectores":      ", ".join(sectores),
                "destino":       ", ".join(paises),
                "fecha":         fecha,
                "estado":        estado,
                "organizador":   "ProCórdoba",
                "fuente_url":    url,
                "fecha_captura": HOY,
            })

        total_pags = 1
        for a in soup.find_all("a", href=True):
            if "pg=" in a.get("href",""):
                try:
                    n = int(a["href"].split("pg=")[-1].split("&")[0])
                    total_pags = max(total_pags, n)
                except ValueError:
                    pass

        return eventos, total_pags

    print(" ProCórdoba...")
    primera, total = scrapear_pagina(1)
    resultados.extend(primera)
    for n in range(2, total + 1):
        tanda, _ = scrapear_pagina(n)
        resultados.extend(tanda)

    print(f"   OK {len(resultados)} registros")
    return resultados


# ─────────────────────────────────────────────
# FUENTE 2: Cancillería  — FIX: filtro de encabezado mejorado
# ─────────────────────────────────────────────
def scrape_cancilleria():
    URL_BASE = "https://exportaciones.cancilleria.gob.ar/Sitios/promociones_poncho/1"
    resultados = []
    url_actual = URL_BASE
    paginas = 0

    print(" Cancillería...")

    while url_actual:
        paginas += 1
        response = requests.get(url_actual, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        tabla = soup.find("table")

        if tabla:
            for fila in tabla.find_all("tr"):
                celdas = fila.find_all("td")
                if len(celdas) < 4:
                    continue

                titulo = celdas[0].get_text(strip=True)

                # FIX: filtra encabezados en todas sus variantes
                if not titulo:
                    continue
                if any(palabra in titulo.upper() for palabra in ["TITULO", "LIMPIAR"]):
                    continue

                sectores = celdas[1].get_text(separator=", ", strip=True)
                sectores = sectores.replace("Menos Info","").replace("Más Info","").strip(", ")
                pais  = celdas[2].get_text(separator=" / ", strip=True)
                fecha = celdas[3].get_text(strip=True)

                # Descarta filas donde fecha no tiene formato de fecha real
                if not fecha or "/" not in fecha:
                    continue

                link = next(
                    (a["href"] for a in fila.find_all("a", href=True)
                     if "cancilleria.gob.ar/es" in a["href"]),
                    ""
                )

                resultados.append({
                    "titulo":        titulo,
                    "tipo":          "Misión Comercial",
                    "sectores":      sectores,
                    "destino":       pais,
                    "fecha":         fecha,
                    "estado":        "",
                    "organizador":   "Cancillería",
                    "fuente_url":    link,
                    "fecha_captura": HOY,
                })

        url_actual = None
        for a in soup.find_all("a", href=True):
            if "next" in a.get("class",[]) or "siguiente" in a.get_text().lower():
                href = a["href"]
                url_actual = href if href.startswith("http") else \
                             "https://exportaciones.cancilleria.gob.ar" + href
                break

        if paginas > 20:
            break

    print(f"   OK {len(resultados)} registros")
    return resultados


# ─────────────────────────────────────────────
# FUENTE 3: PromArgentina  — FIX: filtra basura de navegación
# ─────────────────────────────────────────────
def scrape_argentina_ar():
    URL = "https://argentina.ar/calendario"
    IGNORAR = {"Main navigation", "Calendario", "Inicio", "Servicios",
               "Directorios", "Institucional", "PromArgentina"}
    resultados = []

    print(" PromArgentina...")
    response = requests.get(URL, headers=HEADERS, timeout=15)
    soup = BeautifulSoup(response.text, "html.parser")

    for h2 in soup.find_all("h2"):
        nombre = h2.get_text(strip=True)

        # FIX: descarta elementos de navegación y títulos muy cortos
        if not nombre or len(nombre) < 8 or nombre in IGNORAR:
            continue

        bloque = h2.find_parent()
        partes = [p.strip() for p in bloque.get_text(separator="|", strip=True).split("|") if p.strip()]

        sector = ""
        fecha  = ""
        lugar  = ""

        for parte in partes:
            if len(parte) == 10 and parte.count("/") == 2:
                fecha = parte
            elif "," in parte and len(parte) < 60 and parte != nombre:
                lugar = parte
            elif parte != nombre and len(parte) < 40 and not any(c.isdigit() for c in parte):
                sector = parte

        # FIX: descarta filas sin fecha ni lugar (son nav elements)
        if not fecha and not lugar:
            continue

        a_tag = h2.find_parent("a") or bloque.find("a", href=True)
        link  = ""
        if a_tag:
            href = a_tag.get("href","")
            link = href if href.startswith("http") else "https://argentina.ar" + href

        tipo = "Ronda de Negocios" if "ronda" in nombre.lower() else "Feria Internacional"

        resultados.append({
            "titulo":        nombre,
            "tipo":          tipo,
            "sectores":      sector,
            "destino":       lugar,
            "fecha":         fecha,
            "estado":        "",
            "organizador":   "PromArgentina",
            "fuente_url":    link,
            "fecha_captura": HOY,
        })

    print(f"   OK {len(resultados)} registros")
    return resultados

from playwright.sync_api import sync_playwright
import re as _re

def scrape_cancilleria_ferias():
    URL = "https://exportaciones.cancilleria.gob.ar/sitios_informes/ferias_poncho"
    resultados = []

    print(" Cancillería Ferias...")

    # ── INSTALACIÓN CORRECTA PARA LA NUBE (Sin bloquear la ruta) ──
    import subprocess
    subprocess.run(["playwright", "install", "chromium"])

    with sync_playwright() as p:
        # ── FIX CLAVE: Argumentos para evitar colapso de memoria ──
        nav = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"]
        )
        pag = nav.new_page()
        
        # Le damos 90 segundos porque Cancillería suele saturarse
        pag.goto(URL, timeout=90000)
        pag.wait_for_timeout(5000)

        # Total páginas dinámico
        soup_init = BeautifulSoup(pag.content(), "html.parser")
        total_pags = 1
        for inp in soup_init.find_all("input", {"type": "hidden"}):
            val = inp.get("value", "")
            if val.isdigit() and int(val) > 10:
                total_pags = int(val)
                break

        print(f"   {total_pags} páginas detectadas")

        # Trigger página 1
        campo = pag.locator('input[type="text"]').last
        campo.fill("1")
        campo.press("Enter")
        pag.wait_for_timeout(2000)

        titulos_vistos = set()  # para deduplicar

        for num_pag in range(1, total_pags + 1):
            if num_pag > 1:
                campo = pag.locator('input[type="text"]').last
                campo.fill(str(num_pag))
                campo.press("Enter")
                pag.wait_for_timeout(2000)

            soup = BeautifulSoup(pag.content(), "html.parser")

            for fila in soup.find_all("tr"):
                onclick = fila.get("onclick", "")
                if "ver_oportunidad" not in onclick:
                    continue

                celdas = fila.find_all("td")
                if len(celdas) < 4:
                    continue

                titulo         = celdas[0].get_text(strip=True)
                pais           = celdas[1].get_text(strip=True)
                sector         = celdas[2].get_text(strip=True)
                fecha_apertura = celdas[3].get_text(strip=True)
                fecha_fin      = celdas[4].get_text(strip=True) if len(celdas) > 4 else ""

                # Deduplicación
                clave = titulo.lower().strip()
                if clave in titulos_vistos:
                    continue
                titulos_vistos.add(clave)

                import re as _re
                match = _re.search(r'/sitios/ficha_feriarepre_poncho/(\d+)', onclick)
                link = f"https://exportaciones.cancilleria.gob.ar{match.group(0)}" if match else URL

                resultados.append({
                    "titulo":        titulo,
                    "tipo":          "Feria Internacional",
                    "sectores":      sector,
                    "destino":       pais,
                    "fecha":         f"{fecha_apertura} – {fecha_fin}",
                    "estado":        "",
                    "organizador":   "Cancillería",
                    "fuente_url":    link,
                    "fecha_captura": HOY,
                })

            if num_pag % 20 == 0:
                print(f"   Página {num_pag}/{total_pags} — {len(resultados)} ferias")

        nav.close()

    print(f"   OK {len(resultados)} ferias únicas")
    return resultados
# ─────────────────────────────────────────────
# UNIFICACIÓN
# ─────────────────────────────────────────────
print("\n--- Iniciando scraping unificado ---\n")

todos = []
todos.extend(scrape_procordoba())
todos.extend(scrape_cancilleria())
todos.extend(scrape_argentina_ar())
todos.extend(scrape_cancilleria_ferias())

df = pd.DataFrame(todos, columns=[
    "titulo", "tipo", "sectores", "destino",
    "fecha", "estado", "organizador", "fuente_url", "fecha_captura"
])

import os
os.makedirs("data", exist_ok=True)
df.to_csv("data/misiones_unificadas.csv", index=False, encoding="utf-8-sig")

print("\n-------------------------------------------------------")
print("Misiones unificadas generadas con exito")
print(f"   Total         : {len(df)} registros")
print("   Por organizador:")
try:
    print(df.groupby("organizador").size().to_string())
except Exception:
    pass
print("\n   Muestra ProCordoba (fecha + sectores + estado):")
try:
    pco = df[df["organizador"]=="ProCórdoba"][["titulo","fecha","sectores","estado"]].head(3)
    print(pco.to_string(index=False))
except Exception:
    pass
print("-------------------------------------------------------\n")
