#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EcoPulse Analytics — Aplicación Web Interactiva para Streamlit Community Cloud
==============================================================================
Autor: Matías Rioseco Oróstica
       Ingeniero Comercial | Magíster en Análisis Económico (c), FEN U. de Chile

Archivo principal de despliegue web (`streamlit_app.py`) conectado directamente al
motor analítico de `EcoPulse_Analytics.py`:
  1. Categoría 1: Presentación Profesional y Trayectoria Académica.
  2. Categoría 2: 73 Vistas Macroeconómicas organizadas en 9 Subcategorías (BDE BCCh, INE, DIPRES, BACI-CEPII, Clapes UC, CNEP).
  3. Categoría 3: 8 Vistas de Cotizaciones Financieras y Commodities en Velas Japonesas (OHLC vía Yahoo Finance).
  4. Categoría 4: 7 Vistas de Proyecciones Econométricas (SARIMAX IMACEC, PIB Anual USD con IMACEC Neto YTD, 4 Proyecciones Institucionales y Tablero Resumen en Tarjetas).
  5. Categoría 5: Modelador Estructural Interactivo IS-LM-BP (Mundell-Fleming).
  6. Categoría 6: 3 Instrumentos Interactivos de Cálculo:
     - Calculadora de IPC (Modelo Oficial INE — https://calculadoraipc.ine.cl/)
     - Calculadora de UF (Valores Oficiales Diarios SII — https://www.sii.cl/valores_y_fechas/uf/uf2026.htm)
     - Calculadora de Tipo de Cambio (Conversor Divisas USD, EUR, CLP, UF y UTM — SII / BCCh)
"""

from datetime import date
import io
from pathlib import Path
from typing import Dict, List, Tuple

import importlib.util
import os
import sys

os.environ["ECOPULSE_SKIP_PIP_BOOTSTRAP"] = "1"
if "--no-gui" not in sys.argv:
    sys.argv.append("--no-gui")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


def _cargar_modulo_ecopulse():
    """
    Busca y carga el motor principal sin importar si en GitHub / Windows se guardó
    en minúsculas (`ecopulse_analytics.py`), con mayúsculas (`EcoPulse_Analytics.py`),
    como `cuentas_nacionales_bcch.py` o en una subcarpeta del repositorio.
    """
    if "EcoPulse_Analytics" in sys.modules:
        return sys.modules["EcoPulse_Analytics"]

    dir_actual = Path(__file__).resolve().parent
    directorios_busqueda = [dir_actual, Path.cwd(), dir_actual.parent]
    for sub_d in dir_actual.iterdir():
        if sub_d.is_dir() and not sub_d.name.startswith("."):
            directorios_busqueda.append(sub_d)

    nombres_preferidos = {
        "ecopulse_analytics.py",
        "cuentas_nacionales_bcch.py",
        "ecopulse.py",
    }
    candidato_path = None

    # 1. Búsqueda insensible a mayúsculas/minúsculas (resuelve el error en Linux / Streamlit Cloud)
    for d_busq in directorios_busqueda:
        if not d_busq.is_dir():
            continue
        for archivo_py in sorted(d_busq.glob("*.py")):
            if archivo_py.name == Path(__file__).name:
                continue
            if archivo_py.name.lower() in nombres_preferidos or "ecopulse" in archivo_py.name.lower():
                candidato_path = archivo_py
                break
        if candidato_path is not None:
            break

    # 2. Si tiene otro nombre distinto, buscar cualquier .py que contenga MonitorCuentasNacionales
    if candidato_path is None:
        for d_busq in directorios_busqueda:
            if not d_busq.is_dir():
                continue
            for archivo_py in sorted(d_busq.glob("*.py")):
                if archivo_py.name == Path(__file__).name:
                    continue
                try:
                    txt_head = archivo_py.read_text(encoding="utf-8", errors="ignore")[:80000]
                    if "MonitorCuentasNacionales" in txt_head:
                        candidato_path = archivo_py
                        break
                except Exception:
                    pass
            if candidato_path is not None:
                break

    if candidato_path is not None:
        spec = importlib.util.spec_from_file_location("EcoPulse_Analytics", str(candidato_path))
        if spec is not None and spec.loader is not None:
            mod = importlib.util.module_from_spec(spec)
            sys.modules["EcoPulse_Analytics"] = mod
            spec.loader.exec_module(mod)
            return mod
    return None


ecopulse = _cargar_modulo_ecopulse()


# -----------------------------------------------------------------------------
# 1. CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS (MODO CLARO / MODO OSCURO OBSIDIAN)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="EcoPulse Analytics — Monitor Macroeconómico de Chile",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

if ecopulse is None:
    archivos_en_repo = [p.name for p in Path(__file__).resolve().parent.iterdir() if not p.name.startswith(".")]
    st.error("⚠️ No se encontró el archivo `ecopulse_analytics.py` (o `EcoPulse_Analytics.py`) en tu repositorio de GitHub.")
    st.markdown(
        f"""
        ### Cómo solucionarlo en 30 segundos:
        Actualmente tu repositorio en GitHub (`/mount/src/ecopulse-analytics/`) solo contiene estos archivos: **`{', '.join(archivos_en_repo)}`**

        1. Ve a tu repositorio en **GitHub** ➔ haz clic en **`Add file` ➔ `Upload files`**.
        2. Sube tu archivo **`ecopulse_analytics.py`** (de tu carpeta `c:/Users/Matias/OneDrive/Escritorio/Análisis/app Análisis/ecopulse_analytics.py` o el `EcoPulse_Analytics.py` descargado de aquí) junto a `streamlit_app.py`.
        3. Haz clic en el botón verde **`Commit changes`** (Streamlit Cloud se actualizará solo en 5 segundos).

        ---
        #### 💡 ¿Quieres probarla ahora mismo sin ir a GitHub? Sube tu `ecopulse_analytics.py` aquí abajo:
        """
    )
    archivo_subido = st.file_uploader("Selecciona tu archivo `ecopulse_analytics.py` o `EcoPulse_Analytics.py`:", type=["py"])
    if archivo_subido is not None:
        ruta_destino = Path(__file__).resolve().parent / "EcoPulse_Analytics.py"
        ruta_destino.write_bytes(archivo_subido.getvalue())
        st.success("✓ Archivo cargado correctamente. Iniciando EcoPulse Analytics...")
        st.rerun()
    st.stop()

if "modo_oscuro" not in st.session_state:
    st.session_state["modo_oscuro"] = False
if "categoria_activa" not in st.session_state:
    st.session_state["categoria_activa"] = "2. Vistas Macroeconómicas"
if "vista_macro_clave" not in st.session_state:
    st.session_state["vista_macro_clave"] = "imacec_1"
if "calculadora_activa" not in st.session_state:
    st.session_state["calculadora_activa"] = "calc_ipc"


def _inyectar_estilos_css(oscuro: bool) -> None:
    if oscuro:
        css = """
        <style>
            .stApp { background-color: #0B0F17; color: #F8FAFC; }
            section[data-testid="stSidebar"] { background-color: #0F172A; border-right: 1px solid #263449; }
            .ecopulse-header {
                background: linear-gradient(90deg, #0F172A 0%, #13233F 100%);
                border: 1px solid #0284C7;
                border-radius: 10px;
                padding: 14px 20px;
                margin-bottom: 14px;
                color: #F8FAFC;
            }
            .ecopulse-card {
                background-color: #131C2E;
                border: 1px solid #263449;
                border-radius: 10px;
                padding: 16px;
                margin-bottom: 12px;
                color: #F8FAFC;
            }
            .ecopulse-kpi-box {
                background-color: #19253A;
                border: 1px solid #0284C7;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: center;
                color: #F8FAFC;
            }
        </style>
        """
    else:
        css = """
        <style>
            .ecopulse-header {
                background: linear-gradient(90deg, #0A2540 0%, #0F3D6E 100%);
                border-bottom: 3px solid #D97706;
                border-radius: 10px;
                padding: 14px 20px;
                margin-bottom: 14px;
                color: #FFFFFF;
            }
            .ecopulse-card {
                background-color: #FFFFFF;
                border: 1px solid #CBD5E1;
                border-radius: 10px;
                padding: 16px;
                margin-bottom: 12px;
                color: #0F172A;
                box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
            }
            .ecopulse-kpi-box {
                background-color: #F8FAFC;
                border: 1px solid #0284C7;
                border-radius: 8px;
                padding: 12px 16px;
                text-align: center;
                color: #0F172A;
            }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 2. CARGA Y CACHÉ DE DATOS MACROECONÓMICOS Y MERCADOS (BDE BCCh / INE / YFINANCE)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Cargando series macroeconómicas (BDE Banco Central, INE, DIPRES y Yahoo Finance)...")
def cargar_paquete_datos_web(forzar_online: bool = False) -> Dict[str, object]:
    ecopulse.sincronizar_catalogo_y_contadores_vistas(forzar=True)
    monitor = ecopulse.MonitorCuentasNacionales()
    paquete_base: Dict[str, pd.DataFrame] = {}

    if not forzar_online:
        cache_disco, _ = monitor.cargar_cache_disco(desde="1960-01-01", retornar_vigencia=True)
        if isinstance(cache_disco, dict) and cache_disco:
            paquete_base = cache_disco

    if not paquete_base:
        if forzar_online:
            try:
                paquete_base = monitor.descargar_paquete_cuentas_nacionales(desde="1960-01-01")
            except Exception:
                paquete_base = {}
        if not paquete_base:
            ecopulse._asegurar_respaldo_offline_completo_macro(paquete_base)
            sem_yf = ecopulse.MonitorCuentasNacionales._semilla_mercados_yahoo_instantanea()
            paquete_base.update(sem_yf)

    datos_filtrados = ecopulse.aplicar_filtros_universales(
        datos_base=paquete_base,
        desde="1960-01-01",
        hasta=date.today().strftime("%Y-%m-%d"),
        frecuencia="original",
    )
    return datos_filtrados


def _renderizar_figura_matplotlib_st(fig: plt.Figure) -> None:
    ecopulse.ESTADO_TEMA_Y_MODO_UI["modo_oscuro"] = bool(st.session_state["modo_oscuro"])
    if st.session_state["modo_oscuro"]:
        ecopulse._aplicar_tema_figura_mpl(fig)
    st.pyplot(fig, use_container_width=True, clear_figure=True)
    plt.close(fig)


def _fmt_clp(val: float, dec: int = 0) -> str:
    s = f"{val:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# -----------------------------------------------------------------------------
# 3. BARRA LATERAL (NAVEGACIÓN POR LAS 6 CATEGORÍAS, BUSCADOR Y MODO OSCURO)
# -----------------------------------------------------------------------------
ecopulse.sincronizar_catalogo_y_contadores_vistas()
datos_macro = cargar_paquete_datos_web(forzar_online=False)

with st.sidebar:
    st.markdown(f"### 📊 {ecopulse.APP_NOMBRE}")
    st.caption(f"**{ecopulse.AUTOR_PERFIL['nombre']}**  \n{ecopulse.AUTOR_PERFIL['titular']}")

    modo_osc_toggle = st.toggle(
        "🌙 Modo Oscuro («Obsidian Macro Terminal»)",
        value=bool(st.session_state["modo_oscuro"]),
    )
    st.session_state["modo_oscuro"] = modo_osc_toggle
    ecopulse.ESTADO_TEMA_Y_MODO_UI["modo_oscuro"] = modo_osc_toggle

    if st.button("🔄 Sincronizar Fuentes en Vivo (BDE / SII / Yahoo)", use_container_width=True):
        cargar_paquete_datos_web.clear()
        datos_macro = cargar_paquete_datos_web(forzar_online=True)
        st.success("✓ Series sincronizadas correctamente.")

    st.divider()

    opciones_categorias = [
        "1. Presentación",
        "2. Vistas Macroeconómicas",
        "3. Cotizaciones de Precio",
        "4. Proyecciones",
        "5. Modelación Macroeconómica",
        "6. Calculadoras",
    ]
    cat_sel = st.radio(
        "📂 CATEGORÍAS PRINCIPALES (6):",
        options=opciones_categorias,
        index=opciones_categorias.index(st.session_state["categoria_activa"])
        if st.session_state["categoria_activa"] in opciones_categorias
        else 1,
    )
    st.session_state["categoria_activa"] = cat_sel

    st.divider()
    q_busqueda = st.text_input("🔍 Salto rápido por código o nombre", placeholder="Ej: ACT-16, PROY-07, CALC-01, UF...")
    if q_busqueda.strip():
        clv_directa = ecopulse.resolver_clave_vista_desde_codigo_o_numero(q_busqueda.strip())
        resultados_b = ecopulse.buscar_vistas_en_catalogo(q_busqueda.strip())
        if clv_directa in ("calc_ipc", "calc_uf", "calc_tipo_cambio"):
            if st.button(f"🧮 Ir a {clv_directa.upper()}", use_container_width=True):
                st.session_state["categoria_activa"] = "6. Calculadoras"
                st.session_state["calculadora_activa"] = clv_directa
                st.rerun()
        elif resultados_b:
            for item_b in resultados_b[:5]:
                etq_b = f"[{item_b.get('codigo', '')}] {item_b.get('corto_base', item_b.get('titulo', ''))}"
                if st.button(etq_b, key=f"search_{item_b['clave']}", use_container_width=True):
                    cl_d = str(item_b["clave"])
                    cat_d = str(item_b.get("categoria", ""))
                    if cat_d == "calculadoras":
                        st.session_state["categoria_activa"] = "6. Calculadoras"
                        st.session_state["calculadora_activa"] = cl_d
                    elif cat_d == "presentacion":
                        st.session_state["categoria_activa"] = "1. Presentación"
                    elif cat_d == "cotizaciones":
                        st.session_state["categoria_activa"] = "3. Cotizaciones de Precio"
                        st.session_state["vista_cot_clave"] = cl_d
                    elif cat_d == "proyecciones":
                        st.session_state["categoria_activa"] = "4. Proyecciones"
                        st.session_state["vista_proy_clave"] = cl_d
                    elif cat_d == "modelacion":
                        st.session_state["categoria_activa"] = "5. Modelación Macroeconómica"
                    else:
                        st.session_state["categoria_activa"] = "2. Vistas Macroeconómicas"
                        st.session_state["vista_macro_clave"] = cl_d
                    st.rerun()

_inyectar_estilos_css(bool(st.session_state["modo_oscuro"]))

# Banner institucional superior
st.markdown(
    f"""
    <div class="ecopulse-header">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
            <div>
                <div style="font-size:1.25rem; font-weight:800;">📊 {ecopulse.APP_TITULO_COMPLETO}</div>
                <div style="font-size:0.88rem; opacity:0.90;">
                    {ecopulse.AUTOR_PERFIL['nombre']} — {ecopulse.AUTOR_PERFIL['titular']} | {ecopulse.AUTOR_PERFIL['rol_actual']}
                </div>
            </div>
            <div style="font-size:0.82rem; text-align:right; opacity:0.92;">
                ✉ {ecopulse.AUTOR_PERFIL['email']} &nbsp;|&nbsp; ✆ {ecopulse.AUTOR_PERFIL['telefono']}<br>
                89 Vistas Analíticas + 3 Calculadoras Oficiales (INE / SII / BCCh)
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# 4. RENDERIZADO SEGÚN CATEGORÍA ACTIVA
# -----------------------------------------------------------------------------

# === CATEGORÍA 1: PRESENTACIÓN PROFESIONAL ===
if cat_sel == "1. Presentación":
    st.subheader("👤 1. Presentación Profesional y Sello Analítico")
    st.markdown(
        f"""
        <div class="ecopulse-card">
            <h3 style="margin-top:0;">{ecopulse.AUTOR_PERFIL['nombre']}</h3>
            <p style="font-weight:600; color:#0284C7;">{ecopulse.AUTOR_PERFIL['titular']} &nbsp;•&nbsp; {ecopulse.AUTOR_PERFIL['rol_actual']}</p>
            <p>{ecopulse.AUTOR_PERFIL['resumen']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("#### 💼 Experiencia Profesional e Investigación")
        for cargo, inst, per, det in ecopulse.EXPERIENCIA_PROFESIONAL:
            with st.expander(f"**{cargo}** — {inst} ({per})", expanded=True):
                st.write(det)
    with col_p2:
        st.markdown("#### 🎓 Formación Académica y Postgrado")
        for grado, inst, per, det in ecopulse.FORMACION_ACADEMICA:
            with st.expander(f"**{grado}** — {inst} ({per})", expanded=True):
                st.write(det)


# === CATEGORÍA 2: VISTAS MACROECONÓMICAS (9 SUBCATEGORÍAS • 73 VISTAS) ===
elif cat_sel == "2. Vistas Macroeconómicas":
    subs_lista = ecopulse.SUBCATEGORIAS_MACROECONOMICAS
    mapa_nom_sub = {f"{s['icono']} {s['titulo']} ({s['cantidad_vistas']} vistas)": str(s["clave_sub"]) for s in subs_lista}

    c_nav1, c_nav2, c_nav3, c_nav4 = st.columns([3, 4, 2, 2])
    with c_nav1:
        etq_sub_sel = st.selectbox("Subcategoría Macroeconómica (9):", options=list(mapa_nom_sub.keys()))
        clave_sub_sel = mapa_nom_sub[etq_sub_sel]
    vistas_de_sub = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("subcategoria_clave") == clave_sub_sel]
    mapa_vistas_sub = {f"[{v['codigo']}] {v['titulo_base']}": str(v["clave"]) for v in vistas_de_sub}

    with c_nav2:
        etq_v_sel = st.selectbox("Vista Analítica:", options=list(mapa_vistas_sub.keys()))
        clave_v_macro = mapa_vistas_sub[etq_v_sel]
        st.session_state["vista_macro_clave"] = clave_v_macro

    with c_nav3:
        modo_m = st.radio("Medición:", options=["yoy", "nivel"], format_func=lambda x: "Var. % a/a" if x == "yoy" else "Nivel / Índice", horizontal=True)
        ecopulse.ESTADO_FILTROS_MACRO_BOTONES["modo"] = modo_m

    with c_nav4:
        vent_m = st.selectbox("Horizonte Temporal:", options=["3A", "5A", "10A", "20A", "MAX"], index=2)
        ecopulse.ESTADO_FILTROS_MACRO_BOTONES["ventana"] = vent_m

    fig_m = plt.figure(figsize=(15.0, 8.2), dpi=110)
    ecopulse.dibujar_vista_macro_individual(datos_macro, clave_vista=clave_v_macro, modo=modo_m, fig=fig_m)
    _renderizar_figura_matplotlib_st(fig_m)


# === CATEGORÍA 3: COTIZACIONES DE PRECIO (8 ACTIVOS EN VELAS JAPONESAS OHLC) ===
elif cat_sel == "3. Cotizaciones de Precio":
    vistas_cot = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("categoria") == "cotizaciones"]
    mapa_cot = {f"[{v['codigo']}] {v['corto_base']} — {v['titulo_base']}": str(v["clave"]) for v in vistas_cot}

    cc1, cc2, cc3 = st.columns([4, 2, 2])
    with cc1:
        etq_cot = st.selectbox("Activo Financiero / Commodity (Yahoo Finance):", options=list(mapa_cot.keys()))
        clave_cot = mapa_cot[etq_cot]
    with cc2:
        iv_sel = st.selectbox(
            "Intervalo de Vela Japonesa:",
            options=[c for c, _, _ in ecopulse.OPCIONES_INTERVALO_VELA_YF],
            index=2,
        )
        ecopulse.ESTADO_FILTROS_COTIZACIONES_YF["intervalo_vela"] = iv_sel
    with cc3:
        nv_sel = st.selectbox(
            "Ventana (N° de Velas):",
            options=[n for n, _ in ecopulse.OPCIONES_VENTANA_VELAS_YF],
            index=1,
            format_func=lambda n: "Todas las velas" if n == 0 else f"Últimas {n} velas",
        )
        ecopulse.ESTADO_FILTROS_COTIZACIONES_YF["num_velas"] = int(nv_sel)

    col_act_yf = ecopulse.MAPA_CLAVE_VISTA_A_ACTIVO_YF[clave_cot]
    num_v_cot = str(ecopulse.MAPA_VISTAS_MACRO.get(clave_cot, {}).get("numero", "74"))
    fig_c = plt.figure(figsize=(15.0, 8.2), dpi=110)
    ecopulse.dibujar_vista_cotizacion_individual_yf(
        datos_macro,
        columna_activo=col_act_yf,
        numero_vista=num_v_cot,
        modo="nivel",
        fig=fig_c,
    )
    _renderizar_figura_matplotlib_st(fig_c)


# === CATEGORÍA 4: PROYECCIONES (7 VISTAS + TABLERO EJECUTIVO DE TARJETAS) ===
elif cat_sel == "4. Proyecciones":
    vistas_proy = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("categoria") == "proyecciones"]
    mapa_proy = {f"[{v['codigo']}] {v['corto_base']}": str(v["clave"]) for v in vistas_proy}

    cp1, cp2, cp3, cp4 = st.columns([3, 2, 2, 2])
    with cp1:
        etq_pr = st.selectbox("Vista de Proyección (7):", options=list(mapa_proy.keys()), index=len(mapa_proy) - 1)
        clave_pr = mapa_proy[etq_pr]
    with cp2:
        corte_sel = st.selectbox(
            "Corte Muestral COVID:",
            options=[c for c, _, _ in ecopulse.OPCIONES_CORTE_COVID_SARIMAX],
            format_func=lambda c: dict((k, etq) for k, etq, _ in ecopulse.OPCIONES_CORTE_COVID_SARIMAX).get(c, c),
        )
        ecopulse.ESTADO_FILTROS_PROYECCION_SARIMAX["corte_muestral"] = corte_sel
    with cp3:
        mod_sar = st.selectbox(
            "Especificación SARIMAX:",
            options=[m[0] for m in ecopulse.CATALOGO_MODELOS_SARIMAX_CANDIDATOS],
        )
        ecopulse.ESTADO_FILTROS_PROYECCION_SARIMAX["modelo_etiqueta"] = mod_sar
    with cp4:
        unid_pib = st.selectbox(
            "Unidad / Escala PIB:",
            options=["tco_2018", "yoy_pct", "usd_corriente", "backtest", "tabla"],
            format_func=lambda u: {
                "tco_2018": "Base 2018 (USD Const.)",
                "yoy_pct": "Variación % a/a",
                "usd_corriente": "USD Corrientes",
                "backtest": "Backtest -1 Año vs Real",
                "tabla": "Histórico Completo",
            }.get(u, u),
        )
        ecopulse.ESTADO_FILTROS_PROYECCION_SARIMAX["escala_pib_usd"] = unid_pib

    fig_p = plt.figure(figsize=(15.5, 8.6), dpi=115)
    if clave_pr == "proy_imacec_pulso_yoy":
        ecopulse.dibujar_vista_proyeccion_pulso_imacec_yoy(datos_macro, fig=fig_p)
    elif clave_pr == "proy_imacec_nm_sarimax":
        ecopulse.dibujar_vista_proyeccion_sarimax_imacec_no_minero(datos_macro, fig=fig_p)
    elif clave_pr == "proy_imacec_nm_pulso_yoy":
        ecopulse.dibujar_vista_proyeccion_pulso_imacec_no_minero_yoy(datos_macro, fig=fig_p)
    elif clave_pr == "proy_pib_anual_usd":
        ecopulse.dibujar_vista_proyeccion_pib_anual_usd(datos_macro, fig=fig_p)
    elif clave_pr == "proy_instituciones_4_principales":
        ecopulse.dibujar_vista_4_principales_proyecciones_evolucion(datos_macro, fig=fig_p)
    elif clave_pr == "proy_resumen_mi_proyeccion_vs_otras":
        ecopulse.dibujar_vista_resumen_mi_proyeccion_vs_otras(datos_macro, fig=fig_p)
    else:
        ecopulse.dibujar_vista_proyeccion_sarimax_imacec(datos_macro, fig=fig_p)
    _renderizar_figura_matplotlib_st(fig_p)


# === CATEGORÍA 5: MODELACIÓN MACROECONÓMICA (IS-LM-BP MUNDELL-FLEMING) ===
elif cat_sel == "5. Modelación Macroeconómica":
    cm1, cm2, cm3, cm4 = st.columns(4)
    with cm1:
        reg_mf = st.selectbox("Régimen Cambiario:", ["flexible", "fijo"], format_func=lambda x: "Tipo de Cambio Flexible" if x == "flexible" else "Tipo de Cambio Fijo")
        ecopulse.ESTADO_MODELADOR_ISLM_MF["regimen"] = reg_mf
    with cm2:
        mov_mf = st.selectbox("Movilidad de Capitales:", ["alta", "baja", "perfecta"], format_func=lambda x: f"Movilidad {x.capitalize()}")
        ecopulse.ESTADO_MODELADOR_ISLM_MF["movilidad"] = mov_mf
    with cm3:
        shk_mf = st.selectbox(
            "Shock de Política / Exógeno:",
            ["fiscal_exp", "fiscal_con", "monet_exp", "monet_con", "externo_pos", "riesgo_alza"],
            format_func=lambda s: {
                "fiscal_exp": "Gasto Fiscal Expansivo (+ΔG)",
                "fiscal_con": "Consolidación Fiscal (-ΔG)",
                "monet_exp": "Impulso Monetario (+ΔM / -TPM)",
                "monet_con": "Restricción Monetaria (-ΔM / +TPM)",
                "externo_pos": "Boom Exportador / Cobre (+ΔY*)",
                "riesgo_alza": "Alza Prima por Riesgo (+Δθ)",
            }.get(s, s),
        )
    with cm4:
        int_mf = st.selectbox("Intensidad del Shock:", ["leve", "moderado", "fuerte", "extremo"], index=1)
        ecopulse.ESTADO_MODELADOR_ISLM_MF["shock"] = shk_mf
        ecopulse.ESTADO_MODELADOR_ISLM_MF["intensidad"] = int_mf
        ecopulse._sincronizar_preset_a_parametros_custom_mf(shk_mf, int_mf)

    fig_mf = plt.figure(figsize=(15.5, 8.6), dpi=115)
    ecopulse.dibujar_vista_modelador_islm_mundell_fleming(datos_macro, fig=fig_mf)
    _renderizar_figura_matplotlib_st(fig_mf)


# === CATEGORÍA 6: CALCULADORAS INTERACTIVAS (INSTRUMENTOS DE CÁLCULO INE / SII / BCCh) ===
elif cat_sel == "6. Calculadoras":
    tab_ipc, tab_uf, tab_tc = st.tabs([
        "📈 1. Calculadora de IPC (Modelo Oficial INE)",
        "🏦 2. Calculadora de UF (Valores Oficiales Diarios SII 2026)",
        "💱 3. Calculadora de Tipo de Cambio (Divisas SII / BCCh)",
    ])

    serie_ipc_ine = ecopulse._construir_serie_ipc_empalmada_ine()
    meses_nombres = ecopulse.NOMBRES_MESES_ES

    # -------------------------------------------------------------------------
    # INSTRUMENTO 1: CALCULADORA DE IPC (https://calculadoraipc.ine.cl/)
    # -------------------------------------------------------------------------
    with tab_ipc:
        st.markdown("#### 📈 Calculadora de IPC — Instituto Nacional de Estadísticas (INE)")
        st.caption(
            "Calcula la tasa de variación oficial del Índice de Precios al Consumidor (IPC) entre dos períodos y "
            "actualiza valores monetarios en pesos chilenos ($ CLP), siguiendo la metodología de **calculadoraipc.ine.cl** "
            "(cálculo interno con 12 decimales y variación oficial a 1 decimal)."
        )

        col_ipc_form, col_ipc_res = st.columns([5, 6])
        with col_ipc_form:
            st.markdown("##### 1. Período de Cálculo (Serie Empalmada Oficial Base 2023 = 100)")
            c_i1, c_i2 = st.columns(2)
            with c_i1:
                m_ini_nom = st.selectbox("Mes de Inicio:", meses_nombres, index=8, key="st_ipc_m_ini")
            with c_i2:
                a_ini = st.selectbox("Año de Inicio:", list(range(2026, 1989, -1)), index=1, key="st_ipc_a_ini")

            c_f1, c_f2 = st.columns(2)
            with c_f1:
                m_fin_nom = st.selectbox("Mes de Término:", meses_nombres[:9] if a_ini == 2026 else meses_nombres, index=8, key="st_ipc_m_fin")
            with c_f2:
                a_fin = st.selectbox("Año de Término:", list(range(2026, 1989, -1)), index=0, key="st_ipc_a_fin")

            st.markdown("##### 2. Valor a Ajustar en Pesos Chilenos ($ CLP)")
            monto_ipc_in = st.number_input("Valor a Ajustar ($ CLP):", min_value=0.0, value=1000000.0, step=50000.0, format="%.0f")

            st.markdown("##### 3. Ejemplos Prácticos Oficiales del INE")
            st.info(
                "• **Variación mensual (Sep 2026 vs. Ago 2026)**: **+0,4 %** (113,59 vs. 113,15 pts)\n"
                "• **Variación acumulada en el año (Sep 2026 vs. Dic 2025)**: **+4,0 %** (113,59 vs. 109,26 pts)\n"
                "• **Variación a 12 meses (Sep 2026 vs. Sep 2025)**: **+4,1 %** (113,59 vs. 109,14 pts)"
            )

        with col_ipc_res:
            m_ini = meses_nombres.index(m_ini_nom) + 1
            m_fin = meses_nombres.index(m_fin_nom) + 1
            if (a_fin, m_fin) not in serie_ipc_ine or not np.isfinite(serie_ipc_ine[(a_fin, m_fin)].get("ipc", np.nan)):
                a_fin, m_fin = 2026, 9
                m_fin_nom = meses_nombres[8]
            if (a_ini, m_ini) not in serie_ipc_ine or not np.isfinite(serie_ipc_ine[(a_ini, m_ini)].get("ipc", np.nan)):
                a_ini, m_ini = 2025, 9
                m_ini_nom = meses_nombres[8]

            ipc_0 = float(serie_ipc_ine[(a_ini, m_ini)]["ipc"])
            ipc_1 = float(serie_ipc_ine[(a_fin, m_fin)]["ipc"])
            factor_12d = round(ipc_1 / ipc_0, 12) if ipc_0 > 0 else 1.0
            var_exacta = (factor_12d - 1.0) * 100.0
            var_1d = round(var_exacta, 1)
            monto_ajustado = round(monto_ipc_in * factor_12d)
            dif_pesos = monto_ajustado - round(monto_ipc_in)

            st.markdown(f"##### 📊 Resultado Oficial: {m_ini_nom} {a_ini} ➔ {m_fin_nom} {a_fin}")
            k1, k2, k3 = st.columns(3)
            k1.metric("Valor Ajustado ($ CLP)", f"$ {_fmt_clp(monto_ajustado, 0)}", f"{'+' if dif_pesos >= 0 else '-'}$ {_fmt_clp(abs(dif_pesos), 0)} CLP")
            k2.metric("Variación del Período (INE)", f"{var_1d:+.1f} %".replace(".", ","), f"Exacta: {var_exacta:+.2f}%".replace(".", ","))
            k3.metric("Factor Reajuste (12 dec.)", f"{factor_12d:.6f}".replace(".", ","), f"{ipc_0:.2f} ➔ {ipc_1:.2f} pts")

            st.markdown("##### 📋 Tabla Oficial SII / INE: UTM, UTA e Índice IPC (Base 2023 = 100)")
            anio_tbl_ipc = st.selectbox("Consultar Año en Tabla SII/INE:", [2026, 2025, 2024, 2023, 2022, 2021, 2020], index=0)
            filas_ipc_df = []
            for m_k in range(1, 13):
                d_k = serie_ipc_ine.get((anio_tbl_ipc, m_k), {})
                ipc_v = d_k.get("ipc", np.nan)
                utm_v = d_k.get("utm", np.nan)
                uta_v = d_k.get("uta", np.nan)
                mom_v = d_k.get("mom", np.nan)
                ac_v = d_k.get("acum", np.nan)
                yoy_v = d_k.get("yoy", np.nan)
                filas_ipc_df.append({
                    "Mes": meses_nombres[m_k - 1],
                    "UTM ($)": f"${_fmt_clp(utm_v, 0)}" if np.isfinite(utm_v) else "—",
                    "UTA ($)": f"${_fmt_clp(uta_v, 0)}" if np.isfinite(uta_v) else "—",
                    "IPC (Puntos 2023=100)": f"{ipc_v:.2f}".replace(".", ",") if np.isfinite(ipc_v) else "Pendiente",
                    "Mensual (%)": f"{mom_v:+.1f}%".replace(".", ",") if np.isfinite(mom_v) else "—",
                    "Acumulado Año (%)": f"{ac_v:+.1f}%".replace(".", ",") if np.isfinite(ac_v) else "—",
                    "Últimos 12M (%)": f"{yoy_v:+.1f}%".replace(".", ",") if np.isfinite(yoy_v) else "—",
                })
            st.dataframe(pd.DataFrame(filas_ipc_df), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # INSTRUMENTO 2: CALCULADORA DE UF (https://www.sii.cl/valores_y_fechas/uf/uf2026.htm)
    # -------------------------------------------------------------------------
    with tab_uf:
        st.markdown("#### 🏦 Calculadora de UF — Valores Oficiales Diarios del SII (`uf2026.htm`)")
        st.caption(
            "Convierte entre Unidades de Fomento (UF) y Pesos Chilenos ($ CLP) para cualquier día exacto utilizando "
            "los valores diarios oficiales publicados por el Servicio de Impuestos Internos en **sii.cl/valores_y_fechas/uf/uf2026.htm**."
        )

        col_uf_form, col_uf_tbl = st.columns([5, 6])
        with col_uf_form:
            st.markdown("##### 1. Fecha Exacta del Valor Oficial de la UF (SII)")
            cu1, cu2, cu3 = st.columns(3)
            with cu1:
                d_uf = st.selectbox("Día:", list(range(1, 32)), index=3, key="st_uf_dia")
            with cu2:
                m_uf_nom = st.selectbox("Mes:", meses_nombres[:11], index=10, key="st_uf_mes")
            with cu3:
                a_uf = st.selectbox("Año:", list(range(2026, 2009, -1)), index=0, key="st_uf_anio")

            m_uf = meses_nombres.index(m_uf_nom) + 1
            tbl_uf_sii = ecopulse.obtener_tabla_uf_diaria_oficial_sii(int(a_uf))
            if (m_uf, d_uf) not in tbl_uf_sii:
                d_uf = min(d_uf, 9) if (a_uf == 2026 and m_uf == 11) else 1
            uf_dia_val = tbl_uf_sii.get((m_uf, d_uf), 41268.88)

            st.success(f"**Valor Oficial SII ({d_uf:02d} de {m_uf_nom} de {a_uf})**:  **1 UF = $ {_fmt_clp(uf_dia_val, 2)} CLP**")

            modo_uf_st = st.radio(
                "2. Dirección de Conversión:",
                options=["UF_A_CLP", "CLP_A_UF"],
                format_func=lambda m: "🏦 Convertir de UF ➔ Pesos Chilenos ($ CLP)" if m == "UF_A_CLP" else "💵 Convertir de Pesos Chilenos ($ CLP) ➔ UF",
                horizontal=True,
            )
            val_def_uf = 100.0 if modo_uf_st == "UF_A_CLP" else 1000000.0
            monto_uf_st = st.number_input(
                "Cantidad de UF a convertir:" if modo_uf_st == "UF_A_CLP" else "Monto en Pesos ($ CLP) a convertir:",
                min_value=0.0,
                value=val_def_uf,
                step=10.0 if modo_uf_st == "UF_A_CLP" else 100000.0,
            )

            if modo_uf_st == "UF_A_CLP":
                res_pesos_exacto = monto_uf_st * uf_dia_val
                res_pesos_red = round(res_pesos_exacto)
                u1, u2 = st.columns(2)
                u1.metric("Total en Pesos (2 decimales)", f"$ {_fmt_clp(res_pesos_exacto, 2)} CLP")
                u2.metric("Total Redondeado al Peso", f"$ {_fmt_clp(res_pesos_red, 0)} CLP")
            else:
                res_uf_calc = monto_uf_st / uf_dia_val if uf_dia_val > 0 else 0.0
                u1, u2 = st.columns(2)
                u1.metric("Equivalencia en UF (2 dec.)", f"{_fmt_clp(res_uf_calc, 2)} UF")
                u2.metric("Equivalencia Exacta (6 dec.)", f"{_fmt_clp(res_uf_calc, 6)} UF")

        with col_uf_tbl:
            st.markdown(f"##### 📋 Tabla Oficial Diaria SII — {m_uf_nom} {a_uf} (Formato 3 Columnas SII)")
            filas_sii_3col = []
            for f_i in range(1, 12):
                d1 = f_i if f_i <= 10 else None
                d2 = (f_i + 10) if f_i <= 10 else None
                d3 = (f_i + 20) if (f_i + 20) <= 31 else None
                v1 = tbl_uf_sii.get((m_uf, d1)) if d1 else None
                v2 = tbl_uf_sii.get((m_uf, d2)) if d2 else None
                v3 = tbl_uf_sii.get((m_uf, d3)) if d3 else None
                filas_sii_3col.append({
                    "Día (1–10)": str(d1) if d1 else "",
                    "Valor UF 1–10": f"$ {_fmt_clp(v1, 2)}" if v1 is not None else "—",
                    "Día (11–20)": str(d2) if d2 else "",
                    "Valor UF 11–20": f"$ {_fmt_clp(v2, 2)}" if v2 is not None else "—",
                    "Día (21–31)": str(d3) if d3 else "",
                    "Valor UF 21–31": f"$ {_fmt_clp(v3, 2)}" if v3 is not None else "—",
                })
            st.dataframe(pd.DataFrame(filas_sii_3col), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # INSTRUMENTO 3: CALCULADORA DE TIPO DE CAMBIO (DIVISAS SII / BCCh)
    # -------------------------------------------------------------------------
    with tab_tc:
        st.markdown("#### 💱 Calculadora de Tipo de Cambio — Conversor de Divisas y Unidades (SII / BCCh)")
        monedas_tc = [
            ("USD", "🇺🇸 USD — Dólar Observado (SII / BCCh)", 948.50),
            ("CLP", "🇨🇱 CLP — Peso Chileno ($)", 1.0),
            ("EUR", "🇪🇺 EUR — Euro Oficial (BCCh)", 1035.80),
            ("UF",  "🏦 UF — Unidad de Fomento Oficial (SII)", 41268.88),
            ("UTM", "🏛️ UTM — Unidad Tributaria Mensual (SII)", 72440.0),
            ("BRL", "🇧🇷 BRL — Real Brasileño", 172.90),
            ("CNY", "🇨🇳 CNY — Yuan Chino", 132.30),
            ("GBP", "🇬🇧 GBP — Libra Esterlina", 1242.0),
        ]
        mapa_clp_tc = {cod: val for cod, _, val in monedas_tc}
        etq_tc_map = {cod: etq for cod, etq, _ in monedas_tc}

        col_tc_izq, col_tc_der = st.columns([5, 6])
        with col_tc_izq:
            monto_tc_in = st.number_input("Monto a Convertir:", min_value=0.0, value=1000.0, step=100.0)
            ct1, ct2 = st.columns(2)
            with ct1:
                cod_orig = st.selectbox("De (Moneda Origen):", [c for c, _, _ in monedas_tc], index=0, format_func=lambda c: etq_tc_map[c])
            with ct2:
                cod_dest = st.selectbox("A (Moneda Destino):", [c for c, _, _ in monedas_tc], index=1, format_func=lambda c: etq_tc_map[c])

            usar_tasa_man = st.checkbox("Usar tipo de cambio manual / pactado ($ CLP por unidad)")
            if usar_tasa_man and cod_orig != "CLP":
                mapa_clp_tc[cod_orig] = st.number_input(f"Tipo de cambio manual para 1 {cod_orig} en CLP:", min_value=0.01, value=float(mapa_clp_tc[cod_orig]))

            clp_o = mapa_clp_tc[cod_orig]
            clp_d = mapa_clp_tc[cod_dest]
            tasa_d = clp_o / clp_d
            tasa_i = clp_d / clp_o
            monto_en_clp = monto_tc_in * clp_o
            res_tc = monto_en_clp / clp_d

            st.metric(
                f"Resultado ({cod_orig} ➔ {cod_dest})",
                f"{'$ ' if cod_dest == 'CLP' else ''}{_fmt_clp(res_tc, 0 if cod_dest == 'CLP' else 2)} {cod_dest}",
                f"1 {cod_orig} = {_fmt_clp(tasa_d, 2 if tasa_d >= 10 else 4)} {cod_dest}  |  1 {cod_dest} = {_fmt_clp(tasa_i, 4)} {cod_orig}",
            )

        with col_tc_der:
            st.markdown("##### 🌐 Equivalencia Simultánea de tu Monto en Todas las Unidades")
            eq_cols = st.columns(3)
            for idx_e, (c_e, etq_e, v_e) in enumerate(monedas_tc[:6]):
                val_conv_e = monto_en_clp / mapa_clp_tc[c_e]
                with eq_cols[idx_e % 3]:
                    st.metric(
                        etq_e.split(" — ")[0],
                        f"{'$ ' if c_e == 'CLP' else ''}{_fmt_clp(val_conv_e, 0 if c_e == 'CLP' else 2)} {c_e}",
                        f"Paridad: ${_fmt_clp(mapa_clp_tc[c_e], 2 if c_e != 'CLP' else 0)} CLP",
                    )