import streamlit as st
import pandas as pd
import os
import sys
import subprocess
import base64
import hashlib
from pathlib import Path
from datetime import datetime

# ── Configuración de Página ─────────────────────────────────────
st.set_page_config(
    page_title="Oportunidades Clusters Córdoba",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── API Key (Local usa .env, Streamlit Cloud usa secrets) ─────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

if not os.getenv("PERPLEXITY_API_KEY"):
    try:
        if "PERPLEXITY_API_KEY" in st.secrets:
            os.environ["PERPLEXITY_API_KEY"] = st.secrets["PERPLEXITY_API_KEY"]
    except Exception:
        pass

# ── Paths ─────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

MISIONES_CSV       = DATA_DIR / "misiones_unificadas.csv"
FINANCIAMIENTO_CSV = DATA_DIR / "financiamiento.csv"

# ── Logos ────────────────────────────────────────────────────
LOGO_ACELERA_NAME  = "logo_acelera.png"
LOGO_CLUSTERS_NAME = "logo_clusters.png"

def cargar_b64_logo(nombre_archivo: str) -> str:
    for ruta in [BASE_DIR / nombre_archivo, DATA_DIR / nombre_archivo]:
        if ruta.exists():
            try:
                with open(ruta, "rb") as f:
                    return base64.b64encode(f.read()).decode()
            except Exception:
                pass
    return ""

img_acelera_data  = cargar_b64_logo(LOGO_ACELERA_NAME)
img_clusters_data = cargar_b64_logo(LOGO_CLUSTERS_NAME)

# ── Autenticación ─────────────────────────────────────────────
def hash_pw(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def check_auth():
    if st.session_state.get("authenticated"):
        return

    # Carga logos para la pantalla de login
    img_ac = cargar_b64_logo(LOGO_ACELERA_NAME)
    img_cl = cargar_b64_logo(LOGO_CLUSTERS_NAME)
    logo_ac = f'<img src="data:image/png;base64,{img_ac}" style="height:40px; width:auto;">' if img_ac else ""
    logo_cl = f'<img src="data:image/png;base64,{img_cl}" style="height:44px; width:auto;">' if img_cl else ""

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #f8fafc !important; }
    [data-testid="stHeader"] { background: transparent !important; height: 0px !important; }

    .login-card {
        max-width: 620px;
        margin: 6vh auto 0 auto;
        background: white;
        border-radius: 16px;
        overflow: hidden;
        box-shadow: 0 10px 40px rgba(0,0,0,0.12);
    }
    .login-header {
        background: linear-gradient(135deg, #EC6907 0%, #d45d00 100%);
        padding: 2.5rem 2.5rem 2rem 2.5rem;
    }
    .login-header .login-logos {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1.8rem;
    }
    .login-header .login-title {
        color: white;
        font-size: 2.2rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
        text-align: center;
    }
    .login-header .login-sub {
        color: rgba(255,255,255,0.88);
        font-size: 1rem;
        text-align: center;
        margin: 0;
    }
    .login-body { padding: 2rem 2.5rem 2.5rem 2.5rem; }

    div[data-testid="stButton"] > button {
        background-color: #EC6907 !important;
        color: white !important;
        border: none !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        font-size: 1rem !important;
    }
    div[data-testid="stButton"] > button:hover { background-color: #c85500 !important; }
    </style>
    """, unsafe_allow_html=True)

    # Card centrada con header naranja
    col_l, col_c, col_r = st.columns([1, 4, 1])
    with col_c:
        st.markdown(f"""
        <div class="login-card">
            <div class="login-header">
                <div class="login-title">🔍 Plataforma de Oportunidades</div>
                <div class="login-sub">Monitor de Misiones y Financiamiento · Córdoba Acelera</div>
            </div>
            <div class="login-body">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1.5rem;">
                    {logo_ac}
                    {logo_cl}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        usuario  = st.text_input("Usuario",    placeholder="tu usuario")
        password = st.text_input("Contraseña", type="password", placeholder="••••••••")

        if st.button("Ingresar →", use_container_width=True):
            try:
                users_secrets = dict(st.secrets.get("users", {}))
            except Exception:
                users_secrets = {}

            if not users_secrets:
                env_users_raw = os.getenv("APP_USERS", "")
                for entry in env_users_raw.split(","):
                    if ":" in entry:
                        u, h = entry.strip().split(":", 1)
                        users_secrets[u.strip()] = h.strip()

            if usuario in users_secrets and hash_pw(password) == users_secrets[usuario]:
                st.session_state["authenticated"] = True
                st.session_state["username"] = usuario
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")

    st.stop()

# ── Ejecutar chequeo de auth antes de cualquier contenido ────
check_auth()

# Logout por parámetro de URL
if st.query_params.get("logout") == "true":
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()


# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
    background-color: #f8fafc !important;
    color: #0f172a !important;
}
[data-testid="stAppViewContainer"] {
    padding-top: 50px !important;
    padding-bottom: 80px !important;
}
[data-testid="stHeader"] {
    background: transparent !important;
    height: 0px !important;
}
.fixed-transparent-brand-bar {
    position: fixed !important;
    top: 0 !important; left: 0 !important; right: 0 !important;
    height: 90px !important;
    background-color: transparent !important;
    display: flex !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 0 3.5rem !important;
    z-index: 999999 !important;
    pointer-events: none !important;
}
.fixed-transparent-brand-bar img { pointer-events: auto !important; }
.fixed-transparent-brand-bar .brand-img-left  { height: 52px !important; width: auto !important; object-fit: contain !important; }
.fixed-transparent-brand-bar .brand-img-right { height: 58px !important; width: auto !important; object-fit: contain !important; }
.fixed-bottom-bar {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    height: 50px;
    background-color: #1e293b !important;
    display: flex;
    justify-content: center;
    align-items: center;
    border-top: 1px solid #334155;
    z-index: 999999;
    font-family: system-ui, sans-serif;
    font-size: 0.9rem;
    color: #94a3b8 !important;
}
.fixed-bottom-bar a { color: #f97316 !important; text-decoration: none !important; font-weight: 600; margin-left: 5px; }
.main-header-panel {
    background: linear-gradient(135deg, #EC6907 0%, #d45d00 100%) !important;
    padding: 2.5rem 2rem;
    border-radius: 14px;
    margin-bottom: 2rem;
    margin-top: -5.5rem !important;
    color: #ffffff !important;
    text-align: center;
    box-shadow: 0 10px 25px -5px rgba(236, 105, 7, 0.15);
}
.main-header-panel h1 { color: #ffffff !important; margin: 0 !important; font-size: 2.4rem !important; font-weight: 800 !important; }
.main-header-panel p  { color: rgba(255,255,255,0.95) !important; margin: 0.6rem 0 0 0 !important; font-size: 1.15rem !important; font-weight: 500; }
h3 { color: #0f172a !important; font-weight: 700 !important; }
.custom-update-badge {
    background-color: #f1f5f9 !important;
    color: #334155 !important;
    padding: 0.6rem 1.2rem;
    border-radius: 8px;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    display: inline-block;
    margin-top: 0.4rem;
    border-left: 4px solid #EC6907;
}
div[data-testid="stMetric"] {
    background-color: #ffffff !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
    text-align: center !important;
}
div[data-testid="stMetric"] * { color: #334155 !important; }
div[data-testid="stMetricValue"], div[data-testid="stMetricValue"] > div, div[data-testid="stMetricValue"] * {
    color: #EC6907 !important; font-size: 2.2rem !important; font-weight: 800 !important;
}
div[data-testid="stMetricLabel"] p { color: #475569 !important; font-size: 0.95rem !important; font-weight: 700 !important; text-transform: uppercase !important; }
div[data-testid="stButton"] > button {
    background-color: #EC6907 !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
}
div[data-testid="stButton"] > button:hover { background-color: #c85500 !important; }
div[data-testid="stDownloadButton"] > button {
    background-color: #475569 !important;
    color: #ffffff !important;
    border: none !important;
}
button[data-baseweb="tab"] p { color: #64748b !important; font-weight: 600 !important; }
button[data-baseweb="tab"][aria-selected="true"] p { color: #EC6907 !important; }
label[data-testid="stWidgetLabel"] p { color: #334155 !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# ── Barra superior con logos ──────────────────────────────────
st.markdown(f"""
<div class="fixed-transparent-brand-bar">
    <img class="brand-img-left"  src="data:image/png;base64,{img_acelera_data}"  alt="Córdoba Acelera">
    <img class="brand-img-right" src="data:image/png;base64,{img_clusters_data}" alt="Iniciativa Clusters Córdoba">
</div>
""", unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────
st.markdown("""
<div class="fixed-bottom-bar">
    © 2026 Córdoba Acelera · Iniciativa Clusters Córdoba | Sitio oficial:
    <a href="https://cordobaacelera.com.ar/" target="_blank">cordobaacelera.com.ar</a>
</div>
""", unsafe_allow_html=True)

# ── Header full width con usuario y logout adentro ───────────
username = st.session_state.get("username", "")

st.markdown(f"""
<div class="main-header-panel" style="position: relative;">
    <div style="
        position: absolute;
        top: 1rem;
        right: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1rem;
    ">
        <span style="color: rgba(255,255,255,0.9); font-size: 0.85rem;">
            👤 {username}
        </span>
        <a href="?logout=true" style="
            color: white;
            border: 2px solid rgba(255,255,255,0.7);
            padding: 4px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-decoration: none;
            background: rgba(255,255,255,0.1);
        ">Cerrar sesión</a>
    </div>
    <h1>Plataforma de Oportunidades</h1>
    <p>Monitor de Misiones y Financiamiento para Clusters de Córdoba Acelera</p>
</div>
""", unsafe_allow_html=True)

# ── Helpers de Datos ───────────────────────────────────────────
def ultima_actualizacion(path: Path) -> str:
    if path.exists():
        ts = path.stat().st_mtime
        return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M hs")
    return "Sin datos aún"

def cargar_datos(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    for kwargs in [{"quoting": 1}, {"sep": ";", "on_bad_lines": "skip"}, {"on_bad_lines": "skip"}]:
        try:
            return pd.read_csv(path, **kwargs)
        except Exception:
            continue
    return pd.DataFrame()

def correr_scraper(script_name: str) -> tuple:
    script_path = BASE_DIR / script_name
    env = os.environ.copy()
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True, text=True,
            cwd=str(BASE_DIR), env=env, timeout=360,
        )
        if result.returncode == 0:
            return True, result.stdout
        return False, result.stderr or "Error desconocido"
    except subprocess.TimeoutExpired:
        return False, "Tiempo de espera agotado (6 minutos)"
    except Exception as e:
        return False, str(e)

# ── TABS ──────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["🌍  Misiones · Ferias · Rondas", "💰  Financiamiento"])

# ══════════════════════════════════════════════════════════════
# TAB 1 — MISIONES COMERCIALES
# ══════════════════════════════════════════════════════════════
with tab1:
    col_h, col_b = st.columns([4, 1])
    with col_h:
        st.markdown("### Misiones comerciales, ferias internacionales y rondas de negocios")
        st.markdown(
            f"<div class='custom-update-badge'>📋 Fuentes: ProCórdoba · Cancillería · PromArgentina"
            f" &nbsp;|&nbsp; ⏱️ Última actualización: {ultima_actualizacion(MISIONES_CSV)}</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        st.write("")
        st.write("")
        if st.button("🔄 Actualizar", key="btn_misiones"):
            with st.spinner("Consultando fuentes... (~2 minutos)"):
                ok, msg = correr_scraper("scraper_unificado.py")
            if ok:
                st.success("✅ Misiones actualizadas con éxito")
                st.rerun()
            else:
                st.error(f"Error: {msg[:300]}")

    st.divider()
    df_m = cargar_datos(MISIONES_CSV)

    if df_m.empty:
        st.info("📭 Sin datos. Hacé clic en **🔄 Actualizar** para cargar las misiones.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Oportunidades", len(df_m))
        if "organizador" in df_m.columns: c2.metric("Fuentes", df_m["organizador"].nunique())
        if "tipo"        in df_m.columns: c3.metric("Tipos",   df_m["tipo"].nunique())
        if "destino"     in df_m.columns:
            destinos = df_m["destino"].dropna().str.split(",").explode().str.strip().nunique()
            c4.metric("Destinos", destinos)

        st.write("")
        cf1, cf2, cf3 = st.columns(3)
        with cf1:
            opts = ["Todos"] + sorted(df_m["organizador"].dropna().unique().tolist()) if "organizador" in df_m.columns else ["Todos"]
            f_org = st.selectbox("Filtrar por Organizador", opts)
        with cf2:
            opts2 = ["Todos"] + sorted(df_m["tipo"].dropna().unique().tolist()) if "tipo" in df_m.columns else ["Todos"]
            f_tipo = st.selectbox("Filtrar por Tipo de Evento", opts2)
        with cf3:
            f_text = st.text_input("Búsqueda por palabra clave", placeholder="ej: BIM, Salud, Brasil...")

        dv = df_m.copy()
        if f_org  != "Todos" and "organizador" in dv.columns: dv = dv[dv["organizador"] == f_org]
        if f_tipo != "Todos" and "tipo"        in dv.columns: dv = dv[dv["tipo"]        == f_tipo]
        if f_text: dv = dv[dv.apply(lambda r: f_text.lower() in str(r).lower(), axis=1)]

        cols_show = [c for c in ["titulo","tipo","sectores","destino","fecha","estado","organizador","fuente_url"] if c in dv.columns]
        st.dataframe(dv[cols_show].reset_index(drop=True), use_container_width=True, hide_index=True,
            column_config={
                "titulo":      st.column_config.TextColumn("Título de Oportunidad", width="large"),
                "tipo":        st.column_config.TextColumn("Tipo"),
                "sectores":    st.column_config.TextColumn("Sectores Clave"),
                "destino":     st.column_config.TextColumn("Destino"),
                "fecha":       st.column_config.TextColumn("Fecha Cronograma"),
                "estado":      st.column_config.TextColumn("Estado"),
                "organizador": st.column_config.TextColumn("Fuente Oficial"),
                "fuente_url":  st.column_config.LinkColumn("🔗 Enlace", display_text="Abrir Sitio"),
            })
        st.download_button("⬇️ Descargar CSV", dv.to_csv(index=False).encode("utf-8-sig"), "misiones_clusters.csv", "text/csv")


# ══════════════════════════════════════════════════════════════
# TAB 2 — FINANCIAMIENTO
# ══════════════════════════════════════════════════════════════
with tab2:
    col_h, col_b = st.columns([4, 1])
    with col_h:
        st.markdown("### Convocatorias de financiamiento para clusters y organizaciones")
        st.markdown(
            f"<div class='custom-update-badge'> Monitor Inteligente de 37 Portales (Provincial, Nacional y Multilateral)"
            f" &nbsp;|&nbsp; ⏱️ Última actualización: {ultima_actualizacion(FINANCIAMIENTO_CSV)}</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        st.write("")
        st.write("")
        if st.button("🔄 Actualizar", key="btn_fin"):
            with st.spinner("Consultando motores de IA... (~4 minutos)"):
                ok, msg = correr_scraper("scraper_financiamiento.py")
            if ok:
                st.success("✅ Financiamiento actualizado correctamente")
                st.rerun()
            else:
                st.error(f"Error: {msg[:300]}")

    st.divider()
    df_f = cargar_datos(FINANCIAMIENTO_CSV)

    if df_f.empty:
        st.info("📭 Sin datos. Hacé clic en **🔄 Actualizar** para cargar el financiamiento.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Convocatorias", len(df_f))
        if "estado" in df_f.columns:
            abiertas = df_f["estado"].str.contains("Abierta|Permanente", na=False, case=False).sum()
            c2.metric("Vigentes", int(abiertas))
        if "tipo_fuente"  in df_f.columns: c3.metric("Niveles de Red", df_f["tipo_fuente"].nunique())
        if "organizacion" in df_f.columns: c4.metric("Organismos",     df_f["organizacion"].nunique())

        st.write("")
        cf1, cf2, cf3, cf4 = st.columns(4)
        with cf1:
            opts_n = ["Todos"] + sorted(df_f["tipo_fuente"].dropna().unique().tolist()) if "tipo_fuente" in df_f.columns else ["Todos"]
            f_nivel = st.selectbox("Filtrar por Ámbito/Nivel", opts_n)
        with cf2:
            opts_o = ["Todos"] + sorted(df_f["organizacion"].dropna().unique().tolist()) if "organizacion" in df_f.columns else ["Todos"]
            f_org_f = st.selectbox("Filtrar por Organismo Emisor", opts_o)
        with cf3:
            f_estado = st.selectbox("Filtrar por Estado", ["Todos", "Abierta", "Permanente", "Cerrada"])
        with cf4:
            f_text_f = st.text_input("Búsqueda por palabra clave", placeholder="ej: FONTAR, ANR, clusters...", key="bf")

        dfv = df_f.copy()
        if f_nivel  != "Todos" and "tipo_fuente"  in dfv.columns: dfv = dfv[dfv["tipo_fuente"]  == f_nivel]
        if f_org_f  != "Todos" and "organizacion" in dfv.columns: dfv = dfv[dfv["organizacion"] == f_org_f]
        if f_estado != "Todos" and "estado"        in dfv.columns:
            dfv = dfv[dfv["estado"].str.contains(f_estado, na=False, case=False)]
        if f_text_f: dfv = dfv[dfv.apply(lambda r: f_text_f.lower() in str(r).lower(), axis=1)]

        cols_f = [c for c in ["titulo","tipo","estado","monto","fecha_limite","organizacion","tipo_fuente","link"] if c in dfv.columns]
        st.dataframe(dfv[cols_f].reset_index(drop=True), use_container_width=True, hide_index=True,
            column_config={
                "titulo":       st.column_config.TextColumn("Línea de Financiamiento", width="large"),
                "tipo":         st.column_config.TextColumn("Formato/Instrumento"),
                "estado":       st.column_config.TextColumn("Estado"),
                "monto":        st.column_config.TextColumn("Monto Estimado / Tope"),
                "fecha_limite": st.column_config.TextColumn("Cierre de Convocatoria"),
                "organizacion": st.column_config.TextColumn("Organismo Emisor"),
                "tipo_fuente":  st.column_config.TextColumn("Ámbito"),
                "link":         st.column_config.LinkColumn("🔗 Enlace", display_text="Bases y Condiciones"),
            })
        st.caption("⚠️ Validar vigencias y bases específicas en los sitios oficiales antes de postular.")
        st.download_button("⬇️ Descargar CSV", dfv.to_csv(index=False).encode("utf-8-sig"), "financiamiento_clusters.csv", "text/csv")
