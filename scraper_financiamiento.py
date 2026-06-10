import os
import json
import time
import csv
import requests
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
API_KEY = os.getenv("PERPLEXITY_API_KEY")
HOY = datetime.today().strftime("%Y-%m-%d")

# ── Fuentes con tipo para prompt diferenciado ─────────────────
FUENTES = [
    # Provincial Córdoba
    {"nombre": "Agencia Competitividad Córdoba",    "url": "competitividadcba.org",                                                         "tipo_fuente": "provincial"},
    {"nombre": "Ministerio Producción CBA / CFI",   "url": "cordobaproduce.cba.gov.ar",                                                     "tipo_fuente": "provincial"},
    {"nombre": "Sec. CyT Córdoba",                  "url": "cytcordoba.cba.gov.ar",                                                         "tipo_fuente": "provincial"},
    {"nombre": "Ministerio Industria Córdoba",      "url": "cba.gov.ar/ministerio-de-industria-comercio-y-mineria",                         "tipo_fuente": "provincial"},
    {"nombre": "Innovar y Emprender Córdoba",       "url": "innovaryemprendercba.com.ar",                                                   "tipo_fuente": "provincial"},
    {"nombre": "Bancor",                            "url": "bancor.com.ar/empresas/prestamos",                                              "tipo_fuente": "credito"},
    {"nombre": "Fundación Banco de Córdoba",        "url": "fbco.org.ar",                                                                   "tipo_fuente": "credito"},
    # Nacional ciencia e innovación
    {"nombre": "ANPCyT / Agencia I+D+i",            "url": "argentina.gob.ar/ciencia/agencia/convocatorias",                                "tipo_fuente": "ciencia"},
    {"nombre": "MINCyT",                            "url": "argentina.gob.ar/ciencia/financiamiento/convocatorias-abiertas-cyt",            "tipo_fuente": "ciencia"},
    {"nombre": "CONICET",                           "url": "convocatorias.conicet.gov.ar",                                                  "tipo_fuente": "ciencia"},
    {"nombre": "COFECYT",                           "url": "argentina.gob.ar/ciencia/cofecyt/convocatorias-abiertas",                       "tipo_fuente": "ciencia"},
    {"nombre": "CONFEDI",                           "url": "confedi.org.ar/convocatorias-ciencia-tecnologia",                               "tipo_fuente": "ciencia"},
    {"nombre": "FAN",                               "url": "fan.org.ar/convocatorias",                                                      "tipo_fuente": "ciencia"},
    {"nombre": "INTI",                              "url": "inti.gob.ar/convocatorias",                                                     "tipo_fuente": "ciencia"},
    # Nacional desarrollo productivo
    {"nombre": "SEPYME",                            "url": "argentina.gob.ar/economia/pymes-emprendedores-y-economia-del-conocimiento",     "tipo_fuente": "productivo"},
    {"nombre": "Economía del Conocimiento",         "url": "argentina.gob.ar/servicio/acceder-aportes-no-reembolsables-para-impulsar-o-consolidar-un-nodo-de-la-economia-del", "tipo_fuente": "productivo"},
    {"nombre": "Ministerio Trabajo Nación",         "url": "argentina.gob.ar/trabajo/empresas/programas",                                  "tipo_fuente": "productivo"},
    # Nacional crédito
    {"nombre": "BICE",                              "url": "bice.com.ar/productos",                                                        "tipo_fuente": "credito"},
    {"nombre": "BNA",                               "url": "bna.com.ar/Empresas",                                                          "tipo_fuente": "credito"},
    # Cultura (acotado a industrias creativas)
    {"nombre": "Secretaría de Cultura Nacional",    "url": "argentina.gob.ar/cultura/convocatorias",                                       "tipo_fuente": "cultura"},
    # Internacional / multilateral
    {"nombre": "BID Lab",                           "url": "bidlab.org/es/productos/financiamiento",                                       "tipo_fuente": "multilateral"},
    {"nombre": "BID principal",                     "url": "iadb.org/es/convocatorias",                                                    "tipo_fuente": "multilateral"},
    {"nombre": "CAF",                               "url": "caf.com/es/temas/convocatorias",                                               "tipo_fuente": "multilateral"},
    {"nombre": "PNUD Argentina",                    "url": "undp.org/es/argentina/convocatorias",                                          "tipo_fuente": "multilateral"},
    {"nombre": "GIZ Argentina",                     "url": "giz.de/en/es/argentina",                                                       "tipo_fuente": "multilateral"},
    {"nombre": "Horizonte Europa",     "url": "convocatorias abiertas Horizonte Europa Argentina clusters innovación 2025 2026",           "tipo_fuente": "multilateral"},
    {"nombre": "COSME",                "url": "COSME European Commission open calls SME clusters internationalisation 2025 2026",          "tipo_fuente": "multilateral"},
    {"nombre": "Banco Mundial",        "url": "Banco Mundial convocatorias grants Argentina desarrollo productivo clusters 2025 2026",      "tipo_fuente": "multilateral"},
    {"nombre": "ONUDI",                "url": "UNIDO open calls Argentina industrial clusters development grants 2025 2026",               "tipo_fuente": "multilateral"},
    {"nombre": "IFC",                  "url": "IFC International Finance Corporation funding opportunities Argentina SME 2025 2026",        "tipo_fuente": "multilateral"},
    {"nombre": "AfDB",                 "url": "African Development Bank open calls grants 2025 2026",                                      "tipo_fuente": "multilateral"},
    {"nombre": "APEC",                 "url": "APEC funding opportunities SME clusters projects 2025 2026",                               "tipo_fuente": "multilateral"},
    {"nombre": "KfW",                  "url": "KfW desarrollo Argentina financiamiento proyectos innovación 2025 2026",                    "tipo_fuente": "multilateral"},
    {"nombre": "FONPLATA",             "url": "FONPLATA convocatorias Argentina financiamiento proyectos 2025 2026",                       "tipo_fuente": "multilateral"},
    {"nombre": "AECID",                             "url": "aecid.es/es/convocatorias",                                                    "tipo_fuente": "multilateral"},
    {"nombre": "UE Delegación Argentina",           "url": "eeas.europa.eu/delegations/argentina/convocatorias",                           "tipo_fuente": "multilateral"},
    {"nombre": "TCI Network",                       "url": "tci-network.org/grants",                                                       "tipo_fuente": "multilateral"},
]

# ── Prompts según tipo de fuente ──────────────────────────────
PROMPTS = {
    "provincial": """
Buscá en {url} convocatorias de financiamiento abiertas o vigentes en 2025-2026
para clusters productivos, asociaciones empresariales, organizaciones intermediarias
o agrupamientos de empresas de la provincia de Córdoba, Argentina.
Incluí ANR, créditos blandos, co-inversión y asistencia técnica.
NO incluyas convocatorias ya cerradas antes de 2025.
""",
    "ciencia": """
Buscá en {url} convocatorias abiertas o vigentes en 2025-2026 para proyectos
de innovación, desarrollo tecnológico o investigación aplicada que puedan
aplicar empresas, clusters, asociaciones o agrupamientos productivos de Argentina.
Incluí FONTAR, FONARSEC, ANR y créditos tecnológicos.
NO incluyas becas individuales ni proyectos de investigación básica sin aplicación productiva.
""",
    "productivo": """
Buscá en {url} programas o convocatorias vigentes en 2025-2026 de subsidios,
aportes no reembolsables o créditos para empresas de servicios, economía del
conocimiento, clusters o agrupamientos productivos de Argentina.
NO incluyas programas cerrados antes de 2025.
""",
    "credito": """
Buscá en {url} líneas de crédito o financiamiento disponibles actualmente
para empresas, pymes o asociaciones productivas en Argentina.
Incluí tasas preferenciales, créditos blandos y leasing productivo.
""",
    "cultura": """
Buscá en {url} convocatorias abiertas en 2025-2026 específicamente para
industrias creativas, producción audiovisual, diseño, comunicación o
economía creativa. 
NO incluyas convocatorias de teatro, música, literatura, bibliotecas
ni artes escénicas que no tengan componente de industria o exportación.
""",
    "multilateral": """
Buscá en {url} convocatorias, calls for proposals o programas de financiamiento
abiertos en 2025-2026 para organizaciones, clusters, pymes o gobiernos locales
de América Latina o Argentina específicamente.
Incluí grants, asistencia técnica y préstamos concesionales.
NO incluyas oportunidades laborales ni licitaciones de bienes.
""",
}

# ── Estructura de respuesta esperada ──────────────────────────
FORMATO_JSON = """
Respondé ÚNICAMENTE con JSON válido, sin texto antes ni después:
{
  "convocatorias": [
    {
      "titulo": "nombre exacto de la convocatoria",
      "tipo": "ANR / Crédito / Grant / Co-inversión / Asistencia técnica / Subsidio",
      "monto": "monto si está disponible, sino vacío",
      "fecha_limite": "fecha de cierre si está disponible, sino vacío",
      "estado": "Abierta / Cerrada / Permanente",
      "link": "URL directa a la convocatoria"
    }
  ]
}
Si no encontrás ninguna convocatoria relevante, devolvé: {"convocatorias": []}
"""

# ── Consulta una fuente ───────────────────────────────────────
def consultar_fuente(fuente):
    tipo = fuente.get("tipo_fuente", "productivo")
    prompt_base = PROMPTS.get(tipo, PROMPTS["productivo"])
    prompt = prompt_base.format(url=fuente["url"]) + FORMATO_JSON

    try:
        r = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={"model": "sonar", "messages": [{"role": "user", "content": prompt}]},
            timeout=30
        )
        raw = r.json()
        if "choices" not in raw:
            print(f"   Aviso: {raw.get('error', {}).get('message', raw)}") 
            return []

        contenido = raw["choices"][0]["message"]["content"].strip()
        if "```" in contenido:
            contenido = contenido.split("```")[1]
            if contenido.startswith("json"):
                contenido = contenido[4:]

        return json.loads(contenido).get("convocatorias", [])

    except Exception as e:
        print(f"   Error: {e}") 
        return []


# ── Loop principal ────────────────────────────────────────────
print(f"\n--- Consultando {len(FUENTES)} fuentes ---\n")
todos = []

for i, fuente in enumerate(FUENTES, 1):
    print(f"[{i:02d}/{len(FUENTES)}] {fuente['nombre']}...", end=" ", flush=True)
    convocatorias = consultar_fuente(fuente)

    for c in convocatorias:
        todos.append({
            "titulo":        c.get("titulo", "").strip(),
            "tipo":          c.get("tipo", ""),
            "monto":         c.get("monto", ""),
            "fecha_limite":  c.get("fecha_limite", ""),
            "estado":        c.get("estado", ""),
            "organizacion":  fuente["nombre"],
            "tipo_fuente":   fuente["tipo_fuente"],
            "link":          c.get("link", fuente["url"]),
            "fecha_captura": HOY,
        })

    print(f"{len(convocatorias)} encontrada(s)")
    time.sleep(1)


# ── Limpieza y deduplicación ──────────────────────────────────
df = pd.DataFrame(todos)

if len(df) > 0:
    # Deduplicar por título normalizado
    df["titulo_norm"] = df["titulo"].str.lower().str.strip()
    df = df.drop_duplicates(subset=["titulo_norm"]).drop(columns=["titulo_norm"])

    # Filtrar cerradas sin monto ni link útil
    df = df[~((df["estado"] == "Cerrada") & (df["link"] == "") & (df["monto"] == ""))]

    df = df.reset_index(drop=True)

# ── Guarda con quoting correcto ───────────────────────────────
os.makedirs("data", exist_ok=True)
df.to_csv("data/financiamiento.csv", index=False, encoding="utf-8-sig", quoting=csv.QUOTE_ALL)

print("\n-------------------------------------------------------")
print("Financiamiento CSV generado con exito") # <-- Quitamos ✅
print(f"   Total (sin duplicados): {len(df)}")
if len(df) > 0:
    print(f"\n   Por tipo de fuente:")
    print(df.groupby("tipo_fuente").size().to_string())
    print(f"\n   Por organizacion:")
    print(df.groupby("organizacion").size().sort_values(ascending=False).to_string())
print("-------------------------------------------------------\n")