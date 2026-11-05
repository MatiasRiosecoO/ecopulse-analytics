#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EcoPulse Analytics — Interfaz Web Idéntica a la Aplicación de Escritorio (Streamlit Cloud)
==========================================================================================
Autor: Matías Rioseco Oróstica
       Ingeniero Comercial | Magíster en Análisis Económico (c), FEN U. de Chile

Replica en el navegador la arquitectura visual y de navegación exacta de la aplicación
de escritorio `EcoPulse_Analytics.py`:
  1. Banner Superior Institucional con Identidad, Buscador Rápido y Botón 🌙 Modo Oscuro / ☀️ Modo Claro.
  2. Menú Principal en Grilla de 3×2 Tarjetas Ejecutivas para las 6 Categorías Principales
     (con franja superior de color, insignia de categoría, contador, lista de ítems y botón de acción).
  3. Subpantallas de Navegación en Grilla de 3 Columnas:
     - Categoría 2: Grilla de 3×3 Tarjetas de las 9 Subcategorías Macroeconómicas ➔ Grilla de Vistas.
     - Categorías 3, 4, 5 y 6: Grillas de Tarjetas de Cotizaciones, Proyecciones, Modelación y Calculadoras.
  4. Vista Analítica a Pantalla Completa con Barra de Ruta Interactiva (Breadcrumb:
     ◀ Ant. | Sig. ▶ | 🏠 Menú Principal ▸ Categoría ▸ Subcategoría ▸ Vista Actual) y Botones Rápidos de Filtro.
  5. Las 3 Calculadoras Interactivas Nativas (IPC Oficial INE, UF Oficial Diaria SII 2026 y Tipo de Cambio).
"""

from datetime import date
import importlib.util
import io
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional, Tuple

os.environ["ECOPULSE_SKIP_PIP_BOOTSTRAP"] = "1"
if "--no-gui" not in sys.argv:
    sys.argv.append("--no-gui")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st


# -----------------------------------------------------------------------------
# 1. CARGADOR AUTOMÁTICO INSENSIBLE A MAYÚSCULAS/MINÚSCULAS (LINUX / WINDOWS)
# -----------------------------------------------------------------------------
def _cargar_modulo_ecopulse():
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

st.set_page_config(
    page_title="EcoPulse Analytics — Monitor Macroeconómico de Chile",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if ecopulse is None:
    archivos_en_repo = [p.name for p in Path(__file__).resolve().parent.iterdir() if not p.name.startswith(".")]
    st.error("⚠️ No se encontró el archivo `ecopulse_analytics.py` (o `EcoPulse_Analytics.py`) en tu repositorio de GitHub.")
    st.markdown(
        f"""
        ### Cómo solucionarlo en 30 segundos:
        Actualmente tu repositorio en GitHub (`/mount/src/ecopulse-analytics/`) solo contiene estos archivos: **`{', '.join(archivos_en_repo)}`**

        1. Ve a tu repositorio en **GitHub** ➔ haz clic en **`Add file` ➔ `Upload files`**.
        2. Sube tu archivo **`ecopulse_analytics.py`** (o **`EcoPulse_Analytics.py`**) junto a `streamlit_app.py`.
        3. Haz clic en **`Commit changes`**.

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


# -----------------------------------------------------------------------------
# 2. ESTADO DE NAVEGACIÓN (IDÉNTICO A LA APP DE ESCRITORIO)
# -----------------------------------------------------------------------------
# `pantalla_activa` puede ser:
#   - "menu_categorias"         (Grilla 3x2 con las 6 Categorías Principales)
#   - "sub_macroeconomicas"     (Grilla 3x3 con las 9 Subcategorías Macroeconómicas)
#   - "sub_actividad", "sub_tcr", "sub_inflacion", "sub_empleo", "sub_capital",
#     "sub_finanzas_publicas", "sub_monetaria", "sub_sector_externo", "sub_productividad"
#   - "sub_cotizaciones"        (Grilla con las 8 Vistas de Cotizaciones)
#   - "sub_proyecciones"        (Grilla con las 7 Vistas de Proyecciones)
#   - "sub_modelacion"          (Tarjeta del Modelador IS-LM-BP)
#   - "sub_calculadoras"        (Grilla con los 3 Instrumentos de Cálculo)
#   - "presentacion"            (Vista dedicada de Presentación Profesional)
#   - "calculadoras_hub"        (Suite interactiva con las 3 Calculadoras INE / SII / BCCh)
#   - "vista_analitica"         (Cualquiera de las 89 Vistas Analíticas a pantalla completa)
if "modo_oscuro" not in st.session_state:
    st.session_state["modo_oscuro"] = False
if "pantalla_activa" not in st.session_state:
    st.session_state["pantalla_activa"] = "menu_categorias"
if "vista_actual" not in st.session_state:
    st.session_state["vista_actual"] = "imacec_1"
if "calculadora_activa" not in st.session_state:
    st.session_state["calculadora_activa"] = "calc_ipc"


def ir_a_pantalla(nombre_pantalla: str, clave_vista: Optional[str] = None) -> None:
    st.session_state["pantalla_activa"] = nombre_pantalla
    if clave_vista:
        if clave_vista in ("calc_ipc", "calc_uf", "calc_tipo_cambio"):
            st.session_state["calculadora_activa"] = clave_vista
            st.session_state["pantalla_activa"] = "calculadoras_hub"
        else:
            st.session_state["vista_actual"] = clave_vista


def navegar_a_destino(destino: str) -> None:
    d_norm = destino.strip().lower()
    if d_norm in ("menu", "categorias", "menu_categorias"):
        ir_a_pantalla("menu_categorias")
    elif d_norm == "presentacion":
        ir_a_pantalla("presentacion")
    elif d_norm in ("macroeconomicas", "menu_macro", "sub_macroeconomicas"):
        ir_a_pantalla("sub_macroeconomicas")
    elif d_norm in ecopulse.MAPA_SUBCATEGORIAS_MACRO:
        ir_a_pantalla(d_norm)
    elif d_norm in ("cotizaciones", "menu_cotizaciones", "sub_cotizaciones"):
        ir_a_pantalla("sub_cotizaciones")
    elif d_norm in ("proyecciones", "menu_proyecciones", "sub_proyecciones"):
        ir_a_pantalla("sub_proyecciones")
    elif d_norm in ("modelacion", "menu_modelacion", "sub_modelacion"):
        ir_a_pantalla("sub_modelacion")
    elif d_norm in ("calculadoras", "menu_calculadoras", "sub_calculadoras"):
        ir_a_pantalla("sub_calculadoras")
    elif d_norm in ("calc_ipc", "calc_uf", "calc_tipo_cambio", "calc-01", "calc-02", "calc-03"):
        mapa_c = {"calc-01": "calc_ipc", "calc-02": "calc_uf", "calc-03": "calc_tipo_cambio"}
        ir_a_pantalla("calculadoras_hub", mapa_c.get(d_norm, d_norm))
    else:
        clv_res = ecopulse.resolver_clave_vista_desde_codigo_o_numero(d_norm)
        if clv_res in ("calc_ipc", "calc_uf", "calc_tipo_cambio"):
            ir_a_pantalla("calculadoras_hub", clv_res)
        elif clv_res == "presentacion":
            ir_a_pantalla("presentacion")
        elif clv_res and clv_res in ecopulse.ORDEN_CLAVES_VISTAS:
            ir_a_pantalla("vista_analitica", clv_res)
        elif destino in ecopulse.ORDEN_CLAVES_VISTAS:
            ir_a_pantalla("vista_analitica", destino)


# -----------------------------------------------------------------------------
# 3. ESTILOS CSS PARA REPLICAR LA INTERFAZ DE ESCRITORIO (CLARO Y OBSIDIAN DARK)
# -----------------------------------------------------------------------------
def _aplicar_css_interfaz_escritorio(oscuro: bool) -> None:
    bg_app = "#0B0F17" if oscuro else "#FAFBFD"
    bg_card = "#131C2E" if oscuro else "#FFFFFF"
    bg_subcard = "#19253A" if oscuro else "#F8FAFC"
    borde_card = "#263449" if oscuro else "#CBD5E1"
    txt_prim = "#F8FAFC" if oscuro else "#0F172A"
    txt_sec = "#CBD5E1" if oscuro else "#334155"
    txt_ter = "#94A3B8" if oscuro else "#64748B"

    st.markdown(
        f"""
        <style>
            .block-container {{
                padding-top: 1.0rem !important;
                padding-bottom: 1.2rem !important;
                padding-left: 1.4rem !important;
                padding-right: 1.4rem !important;
                max-width: 100% !important;
            }}
            .stApp {{
                background-color: {bg_app};
                color: {txt_prim};
            }}
            /* Banner institucional idéntico al header_card de la app de escritorio */
            .ep-banner-top {{
                background: linear-gradient(90deg, #07192E 0%, #0F3D6E 100%);
                border: 2px solid #D97706;
                border-radius: 8px;
                padding: 10px 18px;
                margin-bottom: 8px;
                color: #FFFFFF;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }}
            .ep-barra-ruta {{
                background-color: {bg_card};
                border: 1px solid {borde_card};
                border-radius: 6px;
                padding: 8px 14px;
                margin-bottom: 10px;
                color: {txt_prim};
                font-weight: 700;
                font-size: 0.90rem;
            }}
            /* Tarjeta ejecutiva estilo Tkinter card_c con franja superior de color */
            .ep-cat-card {{
                background-color: {bg_card};
                border: 2px solid {borde_card};
                border-radius: 8px;
                overflow: hidden;
                margin-bottom: 4px;
                height: 285px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}
            .ep-cat-stripe {{
                height: 8px;
                width: 100%;
            }}
            .ep-cat-body {{
                padding: 12px 15px;
                flex: 1;
                display: flex;
                flex-direction: column;
            }}
            .ep-badge-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 6px;
            }}
            .ep-badge-num {{
                color: #FFFFFF;
                font-size: 0.72rem;
                font-weight: 800;
                padding: 2px 8px;
                border-radius: 4px;
                letter-spacing: 0.3px;
            }}
            .ep-badge-cnt {{
                font-size: 0.72rem;
                font-weight: 800;
                padding: 2px 8px;
                border-radius: 4px;
            }}
            .ep-cat-title {{
                font-size: 1.08rem;
                font-weight: 800;
                color: {txt_prim};
                margin-bottom: 2px;
            }}
            .ep-cat-sub {{
                font-size: 0.80rem;
                font-weight: 700;
                margin-bottom: 5px;
            }}
            .ep-cat-desc {{
                font-size: 0.77rem;
                color: {txt_sec};
                line-height: 1.32;
                margin-bottom: 7px;
            }}
            .ep-cat-items {{
                background-color: {bg_subcard};
                border: 1px solid {borde_card};
                border-radius: 5px;
                padding: 6px 9px;
                font-size: 0.73rem;
                color: {txt_prim};
                line-height: 1.42;
                margin-top: auto;
            }}
            /* Tarjeta compacta para subcategorías y vistas individuales */
            .ep-vista-card {{
                background-color: {bg_card};
                border: 1.5px solid {borde_card};
                border-radius: 7px;
                overflow: hidden;
                margin-bottom: 3px;
                min-height: 175px;
                display: flex;
                flex-direction: column;
            }}
            div.stButton > button {{
                font-weight: 700 !important;
                border-radius: 6px !important;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# 4. CARGA DE DATOS EN CACHÉ (INSTANTÁNEA)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner="Iniciando motor macroeconómico de EcoPulse Analytics...")
def obtener_datos_macro_en_cache(forzar_online: bool = False) -> Dict[str, object]:
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

    return ecopulse.aplicar_filtros_universales(
        datos_base=paquete_base,
        desde="1960-01-01",
        hasta=date.today().strftime("%Y-%m-%d"),
        frecuencia="original",
    )


def _fmt_clp(val: float, dec: int = 0) -> str:
    s = f"{val:,.{dec}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def _mostrar_figura_mpl(fig: plt.Figure) -> None:
    osc = bool(st.session_state["modo_oscuro"])
    ecopulse.ESTADO_TEMA_Y_MODO_UI["modo_oscuro"] = osc
    if osc:
        ecopulse._aplicar_tema_figura_mpl(fig)
    st.pyplot(fig, use_container_width=True, clear_figure=True)
    plt.close(fig)


resumen_cat = ecopulse.sincronizar_catalogo_y_contadores_vistas()
datos_macro = obtener_datos_macro_en_cache(forzar_online=False)
oscuro_act = bool(st.session_state["modo_oscuro"])
ecopulse.ESTADO_TEMA_Y_MODO_UI["modo_oscuro"] = oscuro_act
_aplicar_css_interfaz_escritorio(oscuro_act)


# -----------------------------------------------------------------------------
# 5. BANNER SUPERIOR INSTITUCIONAL Y BARRA DE CONTROL GLOBAL (SIEMPRE VISIBLE)
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="ep-banner-top">
        <div>
            <div style="font-size:0.80rem; color:#93C5FD; font-weight:700;">📊 {ecopulse.APP_TITULO_COMPLETO}</div>
            <div style="font-size:1.18rem; font-weight:800; color:#FFFFFF; margin:1px 0;">
                {ecopulse.AUTOR_PERFIL['nombre']} &nbsp;—&nbsp; {ecopulse.AUTOR_PERFIL['titular']}
            </div>
            <div style="font-size:0.76rem; color:#FDE68A; font-weight:600;">
                {ecopulse.AUTOR_PERFIL['rol_actual']} &nbsp;|&nbsp; ✉ {ecopulse.AUTOR_PERFIL['email']} &nbsp;|&nbsp; ✆ {ecopulse.AUTOR_PERFIL['telefono']} &nbsp;|&nbsp; ⌖ {ecopulse.AUTOR_PERFIL['ubicacion']}
            </div>
        </div>
        <div style="text-align:right; font-size:0.78rem; color:#E2E8F0;">
            <span style="background:#1E293B; border:1px solid #475569; padding:4px 10px; border-radius:5px; font-weight:700; color:#38BDF8;">
                6 Categorías • 9 Subcategorías • 89 Vistas + 3 Calculadoras
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Barra superior interactiva (Menú Principal | Buscador por Código/Nombre | Actualizar | Modo Oscuro)
col_top_home, col_top_search, col_top_go, col_top_sync, col_top_theme = st.columns([2.2, 4.3, 1.1, 2.2, 2.2])
with col_top_home:
    if st.button("🏠 Menú Principal (6 Categorías)", use_container_width=True, type="primary"):
        ir_a_pantalla("menu_categorias")
        st.rerun()
with col_top_search:
    q_top = st.text_input(
        "Buscador",
        placeholder="🔍 Buscar vista o código (ACT-01..16, EXT-05, PROY-07, CALC-01, UF, IPC...)",
        label_visibility="collapsed",
        key="input_buscador_global",
    )
with col_top_go:
    if st.button("Ir ➔", use_container_width=True):
        if q_top.strip():
            clv_d = ecopulse.resolver_clave_vista_desde_codigo_o_numero(q_top.strip())
            if clv_d:
                navegar_a_destino(clv_d)
                st.rerun()
            else:
                res_b = ecopulse.buscar_vistas_en_catalogo(q_top.strip())
                if res_b:
                    navegar_a_destino(str(res_b[0]["clave"]))
                    st.rerun()
with col_top_sync:
    if st.button("🔄 Actualizar Fuentes (BDE/SII)", use_container_width=True):
        obtener_datos_macro_en_cache.clear()
        datos_macro = obtener_datos_macro_en_cache(forzar_online=True)
        st.toast("✓ Todas las fuentes sincronizadas al día.")
with col_top_theme:
    etq_tema_btn = "☀️ Cambiar a Modo Claro" if oscuro_act else "🌙 Cambiar a Modo Oscuro"
    if st.button(etq_tema_btn, use_container_width=True):
        st.session_state["modo_oscuro"] = not oscuro_act
        st.rerun()

# Si el usuario escribió en el buscador, mostrar tarjetas de resultados inmediatos
if q_top.strip() and st.session_state["pantalla_activa"] != "vista_analitica":
    resultados_busq = ecopulse.buscar_vistas_en_catalogo(q_top.strip())
    if resultados_busq:
        st.markdown(f"##### 🔍 Resultados de búsqueda para «{q_top.strip()}» ({len(resultados_busq)} coincidencias):")
        cols_res = st.columns(3)
        for i_r, it_r in enumerate(resultados_busq[:9]):
            with cols_res[i_r % 3]:
                if st.button(
                    f"{it_r.get('icono', '📊')} [{it_r.get('codigo', '')}] {it_r.get('corto_base', it_r.get('titulo', ''))}",
                    key=f"btn_res_q_{it_r['clave']}_{i_r}",
                    use_container_width=True,
                ):
                    navegar_a_destino(str(it_r["clave"]))
                    st.rerun()
        st.divider()


# -----------------------------------------------------------------------------
# 6. FUNCIÓN AUXILIAR PARA DIBUJAR TARJETAS IDÉNTICAS A LA APP DE ESCRITORIO
# -----------------------------------------------------------------------------
def _renderizar_tarjeta_categoria_o_vista(
    columna_st,
    badge_izq: str,
    badge_der: str,
    icono: str,
    titulo: str,
    subtitulo: str,
    descripcion: str,
    items_lista: List[str],
    color_hex: str,
    bg_suave: str,
    fg_suave: str,
    texto_boton: str,
    key_boton: str,
    callback_fn,
    altura_px: int = 285,
) -> None:
    if st.session_state["modo_oscuro"]:
        bg_suave_eff = "#19253A"
        fg_suave_eff = "#38BDF8"
    else:
        bg_suave_eff = bg_suave
        fg_suave_eff = fg_suave

    items_html = "<br>".join(items_lista) if items_lista else ""
    bloque_items = f'<div class="ep-cat-items">{items_html}</div>' if items_html else ""

    with columna_st:
        st.markdown(
            f"""
            <div class="ep-cat-card" style="height:{altura_px}px;">
                <div class="ep-cat-stripe" style="background-color:{color_hex};"></div>
                <div class="ep-cat-body">
                    <div class="ep-badge-row">
                        <span class="ep-badge-num" style="background-color:{color_hex};">{badge_izq}</span>
                        <span class="ep-badge-cnt" style="background-color:{bg_suave_eff}; color:{fg_suave_eff};">{badge_der}</span>
                    </div>
                    <div class="ep-cat-title">{icono} &nbsp;{titulo}</div>
                    <div class="ep-cat-sub" style="color:{color_hex if not st.session_state['modo_oscuro'] else '#38BDF8'};">{subtitulo}</div>
                    <div class="ep-cat-desc">{descripcion}</div>
                    {bloque_items}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(texto_boton, key=key_boton, use_container_width=True):
            callback_fn()
            st.rerun()


# -----------------------------------------------------------------------------
# 7. ENRUTADOR DE PANTALLAS (MENÚ PRINCIPAL 3x2, SUBPANTALLAS Y VISTAS)
# -----------------------------------------------------------------------------
pantalla = st.session_state["pantalla_activa"]

# =============================================================================
# PANTALLA A: MENÚ PRINCIPAL DE LAS 6 CATEGORÍAS EN GRILLA 3×2 (COMO EN LA APP)
# =============================================================================
if pantalla == "menu_categorias":
    cat_1 = ecopulse.MAPA_CATEGORIAS_PRINCIPALES["presentacion"]
    cat_2 = ecopulse.MAPA_CATEGORIAS_PRINCIPALES["macroeconomicas"]
    cat_3 = ecopulse.MAPA_CATEGORIAS_PRINCIPALES["cotizaciones"]
    cat_4 = ecopulse.MAPA_CATEGORIAS_PRINCIPALES["proyecciones"]
    cat_5 = ecopulse.MAPA_CATEGORIAS_PRINCIPALES["modelacion"]
    cat_6 = ecopulse.MAPA_CATEGORIAS_PRINCIPALES["calculadoras"]

    n_subs_macro = int(resumen_cat["total_subcategorias_macro"])
    n_vistas_macro = int(resumen_cat["total_vistas_macro"])
    n_vistas_cot = int(resumen_cat["total_vistas_cotizaciones"])
    n_vistas_proy = int(resumen_cat["total_vistas_proyecciones"])
    n_vistas_tot = int(resumen_cat["total_vistas_analiticas"])

    st.markdown(
        f"""
        <div class="ep-barra-ruta">
            📂 &nbsp;MENÚ PRINCIPAL &nbsp;▸&nbsp; 6 CATEGORÍAS PRINCIPALES &nbsp;•&nbsp;
            {n_subs_macro} SUBCATEGORÍAS MACRO &nbsp;•&nbsp; {n_vistas_tot} VISTAS NUMERADAS (V-01 A V-{n_vistas_tot:02d}) + 3 CALCULADORAS OFICIALES
        </div>
        """,
        unsafe_allow_html=True,
    )

    tarjetas_6_cats = [
        {
            "badge_izq": str(cat_1["numero_badge"]),
            "badge_der": str(cat_1["etiqueta_cantidad"]),
            "icono": "👤",
            "titulo": str(cat_1["titulo"]),
            "subtitulo": "Perfil Profesional, Sello Analítico y Trayectoria Académica",
            "descripcion": "Perfil profesional, trayectoria laboral e investigación académica de Matías Rioseco Oróstica (Ingeniero Comercial y Magíster en Análisis Económico (c), FEN U. de Chile).",
            "items": [
                "▪ [PRES-01] Perfil Profesional y Sello Analítico",
                "▪ Trayectoria en Economía, Finanzas y Gestión",
                "▪ Formación Académica, Postgrado y Diplomados",
                "▪ Datos de Contacto Directo e Identidad Institucional",
            ],
            "color": "#D97706",
            "bg_s": "#FEF3C7",
            "fg_s": "#92400E",
            "btn": "👤  Abrir 1. Presentación [PRES-01] ➔",
            "dest": "presentacion",
        },
        {
            "badge_izq": str(cat_2["numero_badge"]),
            "badge_der": str(cat_2["etiqueta_cantidad"]),
            "icono": "🏛️",
            "titulo": str(cat_2["titulo"]),
            "subtitulo": f"Monitoreo Macroeconómico ({n_subs_macro} Subcategorías • {n_vistas_macro} Vistas)",
            "descripcion": f"Análisis macroeconómico en {n_subs_macro} subcategorías temáticas ({cat_2['rango_vistas']}) conectadas a la BDE del Banco Central de Chile, INE, DIPRES, BACI-CEPII, Clapes UC y CNEP.",
            "items": [
                "▪ 1. Actividad (16) • 2. TCR (4) • 3. Inflación / IPC (4)",
                "▪ 4. Trabajo y Empleo (12 vistas: EMP-01 a EMP-12)",
                "▪ 5. Capital, Ahorro e Inversión (7) • 6. Finanzas Públicas (8)",
                "▪ 7. Monetaria (4) • 8. Sector Externo (10) • 9. Productividad PTF (8)",
            ],
            "color": "#0F3D6E",
            "bg_s": "#DBEAFE",
            "fg_s": "#1E3A8A",
            "btn": f"🏛️  Explorar {n_vistas_macro} Vistas Macroeconómicas ➔",
            "dest": "sub_macroeconomicas",
        },
        {
            "badge_izq": str(cat_3["numero_badge"]),
            "badge_der": str(cat_3["etiqueta_cantidad"]),
            "icono": "💹",
            "titulo": str(cat_3["titulo"]),
            "subtitulo": f"Monitoreo Financiero, Cambiario y de Commodities ({n_vistas_cot} Vistas)",
            "descripcion": f"Monitoreo bursátil, cambiario, minero y energético ({cat_3['rango_vistas']} • Códigos {cat_3['rango_codigos']}) con gráficos de Velas Japonesas (OHLC) vía Yahoo Finance.",
            "items": [
                "▪ [COT-01..02] 1. Petróleo Brent (USD/bbl) • 2. Dólar USD/CLP",
                "▪ [COT-03..04] 3. Cobre COMEX (USD/lb) • 4. Índice IPSA Chile",
                "▪ [COT-05..06] 5. Oro COMEX (USD/oz) • 6. Molibdeno (USD/lb)",
                "▪ [COT-07..08] 7. Carbonato de Litio (USD/t) • 8. Gas Natural GNL",
            ],
            "color": "#0369A1",
            "bg_s": "#E0F2FE",
            "fg_s": "#0369A1",
            "btn": f"💹  Explorar Cotizaciones [{cat_3['rango_codigos']}] ➔",
            "dest": "sub_cotizaciones",
        },
        {
            "badge_izq": str(cat_4["numero_badge"]),
            "badge_der": str(cat_4["etiqueta_cantidad"]),
            "icono": "🔮",
            "titulo": str(cat_4["titulo"]),
            "subtitulo": f"Modelos Econométricos SARIMAX y Consenso ({n_vistas_proy} Vistas)",
            "descripcion": "Proyecciones econométricas SARIMAX para el IMACEC Total, IMACEC No Minero, PIB Anual en USD (con IMACEC Neto YTD), 4 Proyecciones Institucionales y Resumen en Tarjetas.",
            "items": [
                "▪ [PROY-01..02] IMACEC Total: Senda SARIMAX y Pulso % a/a",
                "▪ [PROY-03] PIB Anual en USD (Alineado con IMACEC Neto YTD)",
                "▪ [PROY-04..05] IMACEC No Minero y [PROY-06] 4 Instituciones",
                "▪ [PROY-07] Tablero Resumen en Tarjetas (2026 y 2027)",
            ],
            "color": "#6D28D9",
            "bg_s": "#F3E8FF",
            "fg_s": "#5B21B6",
            "btn": f"🔮  Explorar Proyecciones [{cat_4['rango_codigos']}] ➔",
            "dest": "sub_proyecciones",
        },
        {
            "badge_izq": str(cat_5["numero_badge"]),
            "badge_der": str(cat_5["etiqueta_cantidad"]),
            "icono": "📐",
            "titulo": str(cat_5["titulo"]),
            "subtitulo": "Equilibrio General IS-LM-BP (Mundell-Fleming)",
            "descripcion": "Simulador estructural interactivo de equilibrio general para economía pequeña y abierta en 4 sistemas interrelacionados bajo Tipo de Cambio Flexible o Fijo.",
            "items": [
                "▪ [MOD-01] 1. Curva Producción – Interés (IS-LM-BP)",
                "▪ 2. Mercado Cambiario y Paridad UIP (Tipo de Cambio – Interés)",
                "▪ 3. Curva de Inversión – Ahorro (Privado, Público y Externo)",
                "▪ 4. Equilibrio Abierto (IS*-LM*) y Exportaciones Netas NX",
            ],
            "color": "#0F766E",
            "bg_s": "#CCFBF1",
            "fg_s": "#115E59",
            "btn": f"📐  Explorar Modelación [{cat_5['rango_codigos']}] ➔",
            "dest": "sub_modelacion",
        },
        {
            "badge_izq": str(cat_6["numero_badge"]),
            "badge_der": str(cat_6["etiqueta_cantidad"]),
            "icono": "🧮",
            "titulo": str(cat_6["titulo"]),
            "subtitulo": "Instrumentos de Cálculo Oficial (INE • SII • BCCh)",
            "descripcion": "Instrumentos interactivos para cálculo de reajustabilidad por IPC (modelo INE), conversión diaria de UF (tabla oficial SII 2026) y conversión de divisas.",
            "items": [
                "▪ [CALC-01] 1. Calculadora de IPC (Modelo Oficial INE — calculadoraipc.ine.cl)",
                "▪ [CALC-02] 2. Calculadora de UF (Valores Oficiales Diarios SII — uf2026.htm)",
                "▪ [CALC-03] 3. Calculadora de Tipo de Cambio (USD, EUR, CLP, UF y UTM)",
                "▪ Formularios interactivos + Tablas oficiales SII e INE",
            ],
            "color": "#0284C7",
            "bg_s": "#E0F2FE",
            "fg_s": "#0369A1",
            "btn": "🧮  Explorar Calculadoras [CALC-01..CALC-03] ➔",
            "dest": "sub_calculadoras",
        },
    ]

    for fila_idx in range(2):
        cols_3 = st.columns(3)
        for col_idx in range(3):
            item_c = tarjetas_6_cats[fila_idx * 3 + col_idx]
            dest_c = item_c["dest"]
            _renderizar_tarjeta_categoria_o_vista(
                columna_st=cols_3[col_idx],
                badge_izq=item_c["badge_izq"],
                badge_der=item_c["badge_der"],
                icono=item_c["icono"],
                titulo=item_c["titulo"],
                subtitulo=item_c["subtitulo"],
                descripcion=item_c["descripcion"],
                items_lista=item_c["items"],
                color_hex=item_c["color"],
                bg_suave=item_c["bg_s"],
                fg_suave=item_c["fg_s"],
                texto_boton=item_c["btn"],
                key_boton=f"btn_cat_main_{dest_c}",
                callback_fn=lambda d=dest_c: navegar_a_destino(d),
                altura_px=290,
            )


# =============================================================================
# PANTALLA B: SUBPANTALLA DE LAS 9 SUBCATEGORÍAS MACROECONÓMICAS (GRILLA 3×3)
# =============================================================================
elif pantalla == "sub_macroeconomicas":
    c_back, c_tit = st.columns([2.2, 7.8])
    with c_back:
        if st.button("⬅ Volver a las 6 Categorías", use_container_width=True):
            ir_a_pantalla("menu_categorias")
            st.rerun()
    with c_tit:
        st.markdown(
            """
            <div class="ep-barra-ruta">
                🏛️ &nbsp;CATEGORÍA 2: VISTAS MACROECONÓMICAS &nbsp;—&nbsp; 9 Subcategorías Temáticas • 73 Vistas Individuales (Vistas 1–73)
            </div>
            """,
            unsafe_allow_html=True,
        )

    subs_macro = ecopulse.SUBCATEGORIAS_MACROECONOMICAS
    for f_s in range(0, len(subs_macro), 3):
        cols_s = st.columns(3)
        for c_s in range(3):
            if f_s + c_s >= len(subs_macro):
                break
            sub_info = subs_macro[f_s + c_s]
            clv_sub = str(sub_info["clave_sub"])
            vistas_s = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("subcategoria_clave") == clv_sub]
            items_s = [f"▪ [{v['codigo']}] {v['corto_base']}" for v in vistas_s[:4]]
            if len(vistas_s) > 4:
                items_s.append(f"▪ ... y {len(vistas_s) - 4} vistas adicionales ({sub_info['rango_codigos']})")
            _renderizar_tarjeta_categoria_o_vista(
                columna_st=cols_s[c_s],
                badge_izq=f"SUBCATEGORÍA 2.{sub_info['numero']}",
                badge_der=str(sub_info["etiqueta_cantidad"]),
                icono=str(sub_info["icono"]),
                titulo=str(sub_info["titulo"]),
                subtitulo=f"Códigos {sub_info['rango_codigos']} ({sub_info['rango_vistas']})",
                descripcion=str(sub_info["descripcion"]),
                items_lista=items_s,
                color_hex=str(sub_info["color"]),
                bg_suave="#EFF6FF",
                fg_suave=str(sub_info["color"]),
                texto_boton=f"{sub_info['icono']}  Abrir {sub_info['nombre_limpio']} ({sub_info['cantidad_vistas']} Vistas) ➔",
                key_boton=f"btn_sub_macro_{clv_sub}",
                callback_fn=lambda k=clv_sub: ir_a_pantalla(k),
                altura_px=275,
            )


# =============================================================================
# PANTALLA C: GRILLA DE TARJETAS DE VISTAS DE UNA SUBCATEGORÍA O CATEGORÍA
# =============================================================================
elif pantalla in ecopulse.MAPA_SUBCATEGORIAS_MACRO or pantalla in ("sub_cotizaciones", "sub_proyecciones", "sub_modelacion", "sub_calculadoras"):
    es_sub_macro = pantalla in ecopulse.MAPA_SUBCATEGORIAS_MACRO
    c_b1, c_b2 = st.columns([2.4, 7.6])
    with c_b1:
        if es_sub_macro:
            if st.button("⬅ Volver a las 9 Subcategorías Macro", use_container_width=True):
                ir_a_pantalla("sub_macroeconomicas")
                st.rerun()
        else:
            if st.button("⬅ Volver a las 6 Categorías", use_container_width=True):
                ir_a_pantalla("menu_categorias")
                st.rerun()

    if es_sub_macro:
        info_hdr = ecopulse.MAPA_SUBCATEGORIAS_MACRO[pantalla]
        txt_hdr = f"{info_hdr['icono']} &nbsp;2.{info_hdr['numero']} {info_hdr['nombre_limpio'].upper()} &nbsp;—&nbsp; {info_hdr['etiqueta_cantidad']}"
        lista_tarjetas = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("subcategoria_clave") == pantalla]
    elif pantalla == "sub_cotizaciones":
        txt_hdr = "💹 &nbsp;CATEGORÍA 3: COTIZACIONES DE PRECIO &nbsp;—&nbsp; 8 Vistas en Velas Japonesas (COT-01 a COT-08)"
        lista_tarjetas = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("categoria") == "cotizaciones"]
    elif pantalla == "sub_proyecciones":
        txt_hdr = "🔮 &nbsp;CATEGORÍA 4: PROYECCIONES ECONOMÉTRICAS Y CONSENSO &nbsp;—&nbsp; 7 Vistas (PROY-01 a PROY-07)"
        lista_tarjetas = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("categoria") == "proyecciones"]
    elif pantalla == "sub_modelacion":
        txt_hdr = "📐 &nbsp;CATEGORÍA 5: MODELACIÓN MACROECONÓMICA &nbsp;—&nbsp; Modelador IS-LM-BP (MOD-01)"
        lista_tarjetas = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("categoria") == "modelacion"]
    else:
        txt_hdr = "🧮 &nbsp;CATEGORÍA 6: CALCULADORAS INTERACTIVAS OFICIALES &nbsp;—&nbsp; 3 Instrumentos de Cálculo (CALC-01 a CALC-03)"
        lista_tarjetas = ecopulse.CATALOGO_INSTRUMENTOS_CALCULADORAS

    with c_b2:
        st.markdown(f'<div class="ep-barra-ruta">{txt_hdr}</div>', unsafe_allow_html=True)

    for idx_v in range(0, len(lista_tarjetas), 3):
        cols_v = st.columns(3)
        for c_i in range(3):
            if idx_v + c_i >= len(lista_tarjetas):
                break
            v_meta = lista_tarjetas[idx_v + c_i]
            clv_dest = str(v_meta["clave"])
            cod_v = str(v_meta.get("codigo", ""))
            num_v = str(v_meta.get("numero", ""))
            tit_v = str(v_meta.get("titulo_base", v_meta.get("titulo", "")))
            corto_v = str(v_meta.get("corto_base", tit_v))
            sub_v = str(v_meta.get("subtitulo", ""))
            col_v = str(v_meta.get("color_acento", "#0284C7"))
            es_calc = pantalla == "sub_calculadoras"
            _renderizar_tarjeta_categoria_o_vista(
                columna_st=cols_v[c_i],
                badge_izq=f"CÓD: {cod_v}" if es_calc else f"CÓD: {cod_v} • VISTA {num_v}",
                badge_der="INSTRUMENTO INTERACTIVO" if es_calc else str(v_meta.get("codigo_global", f"V-{num_v}")),
                icono=str(v_meta.get("icono", "📊")),
                titulo=corto_v,
                subtitulo=tit_v[:88] + ("..." if len(tit_v) > 88 else ""),
                descripcion=sub_v[:175] + ("..." if len(sub_v) > 175 else ""),
                items_lista=[],
                color_hex=col_v,
                bg_suave="#E0F2FE",
                fg_suave="#0369A1",
                texto_boton=f"🧮  Abrir {corto_v} [{cod_v}] ➔" if es_calc else f"📊  Abrir Vista {num_v} [{cod_v}] ➔",
                key_boton=f"btn_card_v_{clv_dest}",
                callback_fn=(lambda k=clv_dest: ir_a_pantalla("calculadoras_hub", k)) if es_calc else (lambda k=clv_dest: ir_a_pantalla("vista_analitica", k)),
                altura_px=220,
            )


# =============================================================================
# PANTALLA D: VISTA DE PRESENTACIÓN PROFESIONAL (CATEGORÍA 1)
# =============================================================================
elif pantalla == "presentacion":
    c_nav_p1, c_nav_p2, c_nav_p3, c_nav_p4 = st.columns(4)
    with c_nav_p1:
        if st.button("🏠 Volver al Menú Principal", use_container_width=True):
            ir_a_pantalla("menu_categorias")
            st.rerun()
    with c_nav_p2:
        if st.button("🏛️ Ir a 2. Vistas Macroeconómicas ➔", use_container_width=True):
            ir_a_pantalla("sub_macroeconomicas")
            st.rerun()
    with c_nav_p3:
        if st.button("🔮 Ir a 4. Proyecciones ➔", use_container_width=True):
            ir_a_pantalla("sub_proyecciones")
            st.rerun()
    with c_nav_p4:
        if st.button("🧮 Ir a 6. Calculadoras ➔", use_container_width=True):
            ir_a_pantalla("calculadoras_hub", "calc_ipc")
            st.rerun()

    st.markdown(
        f"""
        <div class="ep-barra-ruta">
            👤 &nbsp;CATEGORÍA 1: PRESENTACIÓN PROFESIONAL [PRES-01] &nbsp;—&nbsp; {ecopulse.AUTOR_PERFIL['nombre']}
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.info(ecopulse.AUTOR_PERFIL["resumen"])
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("#### 💼 Trayectoria Profesional e Investigación")
        for item_exp in ecopulse.AUTOR_PERFIL.get("experiencia", []):
            if isinstance(item_exp, (tuple, list)) and len(item_exp) >= 2:
                tit_e, det_e = item_exp[0], item_exp[1]
                with st.expander(f"**{tit_e}**", expanded=True):
                    st.write(det_e)
            else:
                st.markdown(f"- {item_exp}")
    with col_p2:
        st.markdown("#### 🎓 Formación Académica y Postgrado")
        for item_form in ecopulse.AUTOR_PERFIL.get("formacion", []):
            if isinstance(item_form, (tuple, list)) and len(item_form) >= 2:
                with st.expander(f"**{item_form[0]}**", expanded=True):
                    st.write(item_form[1])
            else:
                st.markdown(f"🎓 **{item_form}**")


# =============================================================================
# PANTALLA E: CATEGORÍA 6 — SUITE DE 3 CALCULADORAS INTERACTIVAS (INE / SII / BCCh)
# =============================================================================
elif pantalla == "calculadoras_hub":
    c_cb1, c_cb2, c_cb3, c_cb4, c_cb5 = st.columns([1.8, 1.8, 2.2, 2.2, 2.2])
    with c_cb1:
        if st.button("🏠 Menú Principal", key="calc_home_btn", use_container_width=True):
            ir_a_pantalla("menu_categorias")
            st.rerun()
    with c_cb2:
        if st.button("📂 6. Calculadoras", key="calc_cat_btn", use_container_width=True):
            ir_a_pantalla("sub_calculadoras")
            st.rerun()
    with c_cb3:
        if st.button("📈 1. Calculadora IPC (INE)", type="primary" if st.session_state["calculadora_activa"] == "calc_ipc" else "secondary", use_container_width=True):
            st.session_state["calculadora_activa"] = "calc_ipc"
            st.rerun()
    with c_cb4:
        if st.button("🏦 2. Calculadora UF (SII 2026)", type="primary" if st.session_state["calculadora_activa"] == "calc_uf" else "secondary", use_container_width=True):
            st.session_state["calculadora_activa"] = "calc_uf"
            st.rerun()
    with c_cb5:
        if st.button("💱 3. Calculadora Tipo de Cambio", type="primary" if st.session_state["calculadora_activa"] == "calc_tipo_cambio" else "secondary", use_container_width=True):
            st.session_state["calculadora_activa"] = "calc_tipo_cambio"
            st.rerun()

    serie_ipc_ine = ecopulse._construir_serie_ipc_empalmada_ine()
    meses_nombres = ecopulse.NOMBRES_MESES_ES
    calc_act = st.session_state["calculadora_activa"]

    # --- 1. CALCULADORA DE IPC (MODELO OFICIAL INE — calculadoraipc.ine.cl) ---
    if calc_act == "calc_ipc":
        st.markdown(
            '<div class="ep-barra-ruta" style="border-left:5px solid #D97706;">📈 &nbsp;[CALC-01] CALCULADORA DE IPC — INSTITUTO NACIONAL DE ESTADÍSTICAS (calculadoraipc.ine.cl)</div>',
            unsafe_allow_html=True,
        )
        col_ipc_form, col_ipc_res = st.columns([5, 6])
        with col_ipc_form:
            st.markdown("##### 1. Período de Cálculo (Serie Empalmada Oficial Base 2023 = 100)")
            if "ipc_m_ini_idx" not in st.session_state:
                st.session_state["ipc_m_ini_idx"] = 8
                st.session_state["ipc_a_ini_val"] = 2025
                st.session_state["ipc_m_fin_idx"] = 8
                st.session_state["ipc_a_fin_val"] = 2026
                st.session_state["ipc_monto_val"] = 1000000.0

            c_i1, c_i2 = st.columns(2)
            with c_i1:
                m_ini_nom = st.selectbox("📅 Mes de Inicio:", meses_nombres, index=int(st.session_state["ipc_m_ini_idx"]))
            with c_i2:
                anios_l = list(range(2026, 1989, -1))
                a_ini = st.selectbox("📅 Año de Inicio:", anios_l, index=anios_l.index(int(st.session_state["ipc_a_ini_val"])))

            c_f1, c_f2 = st.columns(2)
            with c_f1:
                m_fin_nom = st.selectbox("📅 Mes de Término:", meses_nombres, index=int(st.session_state["ipc_m_fin_idx"]))
            with c_f2:
                a_fin = st.selectbox("📅 Año de Término:", anios_l, index=anios_l.index(int(st.session_state["ipc_a_fin_val"])))

            st.markdown("##### 2. Valor a Ajustar en Pesos Chilenos ($ CLP)")
            monto_ipc_in = st.number_input("Valor a Ajustar ($ CLP):", min_value=0.0, value=float(st.session_state["ipc_monto_val"]), step=50000.0, format="%.0f")

            st.markdown("##### 3. Ejemplos Oficiales de `calculadoraipc.ine.cl` (1 Clic):")
            ce1, ce2, ce3 = st.columns(3)
            with ce1:
                if st.button("📌 Var. Mensual (Ago➔Sep 2026)", use_container_width=True):
                    st.session_state["ipc_m_ini_idx"], st.session_state["ipc_a_ini_val"] = 7, 2026
                    st.session_state["ipc_m_fin_idx"], st.session_state["ipc_a_fin_val"] = 8, 2026
                    st.rerun()
            with ce2:
                if st.button("📌 Acumulada Año (Dic 25➔Sep 26)", use_container_width=True):
                    st.session_state["ipc_m_ini_idx"], st.session_state["ipc_a_ini_val"] = 11, 2025
                    st.session_state["ipc_m_fin_idx"], st.session_state["ipc_a_fin_val"] = 8, 2026
                    st.rerun()
            with ce3:
                if st.button("📌 Anual 12M (Sep 25➔Sep 26)", use_container_width=True):
                    st.session_state["ipc_m_ini_idx"], st.session_state["ipc_a_ini_val"] = 8, 2025
                    st.session_state["ipc_m_fin_idx"], st.session_state["ipc_a_fin_val"] = 8, 2026
                    st.rerun()

            st.caption(
                "Nota Metodológica INE: Internamente se realizan los cálculos con 12 decimales sobre las series "
                "empalmadas para fines de reajustabilidad. La variación oficial presentada es a un decimal."
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

            st.markdown(f"##### 📊 Resultado Oficial INE: {m_ini_nom} {a_ini} ➔ {m_fin_nom} {a_fin}")
            k1, k2, k3 = st.columns(3)
            k1.metric("Valor Ajustado ($ CLP)", f"$ {_fmt_clp(monto_ajustado, 0)}", f"{'+' if dif_pesos >= 0 else '-'}$ {_fmt_clp(abs(dif_pesos), 0)} CLP")
            k2.metric("Variación del Período (INE)", f"{var_1d:+.1f} %".replace(".", ","), f"Exacta: {var_exacta:+.2f}%".replace(".", ","))
            k3.metric("Factor (12 decimales)", f"{factor_12d:.6f}".replace(".", ","), f"{ipc_0:.2f} ➔ {ipc_1:.2f} pts")

            st.markdown("##### 📋 Tabla Oficial SII / INE: UTM, UTA e Índice IPC (Base 2023 = 100)")
            anio_tbl_ipc = st.selectbox("Año en Tabla SII/INE:", [2026, 2025, 2024, 2023, 2022, 2021, 2020], index=0)
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
                    "IPC (Puntos)": f"{ipc_v:.2f}".replace(".", ",") if np.isfinite(ipc_v) else "Pendiente",
                    "Mensual (%)": f"{mom_v:+.1f}%".replace(".", ",") if np.isfinite(mom_v) else "—",
                    "Acum. Año (%)": f"{ac_v:+.1f}%".replace(".", ",") if np.isfinite(ac_v) else "—",
                    "Últ. 12M (%)": f"{yoy_v:+.1f}%".replace(".", ",") if np.isfinite(yoy_v) else "—",
                })
            st.dataframe(pd.DataFrame(filas_ipc_df), use_container_width=True, hide_index=True)

    # --- 2. CALCULADORA DE UF (VALORES OFICIALES SII — sii.cl/valores_y_fechas/uf/uf2026.htm) ---
    elif calc_act == "calc_uf":
        st.markdown(
            '<div class="ep-barra-ruta" style="border-left:5px solid #059669;">🏦 &nbsp;[CALC-02] CALCULADORA DE UF — VALORES DIARIOS OFICIALES SII (sii.cl/valores_y_fechas/uf/uf2026.htm)</div>',
            unsafe_allow_html=True,
        )
        col_uf_form, col_uf_tbl = st.columns([5, 6])
        with col_uf_form:
            st.markdown("##### 1. Selecciona la Fecha Exacta del Valor Oficial de la UF (SII)")
            cu1, cu2, cu3 = st.columns(3)
            with cu1:
                d_uf = st.selectbox("Día:", list(range(1, 32)), index=3)
            with cu2:
                m_uf_nom = st.selectbox("Mes:", meses_nombres[:11], index=10)
            with cu3:
                a_uf = st.selectbox("Año:", list(range(2026, 2009, -1)), index=0)

            m_uf = meses_nombres.index(m_uf_nom) + 1
            tbl_uf_sii = ecopulse.obtener_tabla_uf_diaria_oficial_sii(int(a_uf))
            if (m_uf, d_uf) not in tbl_uf_sii:
                d_uf = min(d_uf, 9) if (a_uf == 2026 and m_uf == 11) else 1
            uf_dia_val = tbl_uf_sii.get((m_uf, d_uf), 41268.88)

            st.success(f"**1 UF Oficial SII ({d_uf:02d} de {m_uf_nom} de {a_uf})  =  $ {_fmt_clp(uf_dia_val, 2)} CLP**")

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

    # --- 3. CALCULADORA DE TIPO DE CAMBIO (DIVISAS SII / BCCh) ---
    else:
        st.markdown(
            '<div class="ep-barra-ruta" style="border-left:5px solid #0284C7;">💱 &nbsp;[CALC-03] CALCULADORA DE TIPO DE CAMBIO — CONVERSOR MULTIMONEDA (SII / BCCh)</div>',
            unsafe_allow_html=True,
        )
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
            for idx_e, (c_e, etq_e, _) in enumerate(monedas_tc[:6]):
                val_conv_e = monto_en_clp / mapa_clp_tc[c_e]
                with eq_cols[idx_e % 3]:
                    st.metric(
                        etq_e.split(" — ")[0],
                        f"{'$ ' if c_e == 'CLP' else ''}{_fmt_clp(val_conv_e, 0 if c_e == 'CLP' else 2)} {c_e}",
                        f"Paridad: ${_fmt_clp(mapa_clp_tc[c_e], 2 if c_e != 'CLP' else 0)} CLP",
                    )


# =============================================================================
# PANTALLA F: VISTA ANALÍTICA A PANTALLA COMPLETA CON BREADCRUMB INTERACTIVO
# =============================================================================
else:
    clave_v = st.session_state["vista_actual"]
    if clave_v not in ecopulse.ORDEN_CLAVES_VISTAS:
        clave_v = ecopulse.ORDEN_CLAVES_VISTAS[0]
        st.session_state["vista_actual"] = clave_v

    idx_v = ecopulse.ORDEN_CLAVES_VISTAS.index(clave_v)
    info_r = ecopulse.obtener_ruta_navegacion_vista(clave_v)
    cat_k = info_r["categoria_clave"]
    sub_k = info_r["subcategoria_clave"]

    # Barra Superior de Ruta Interactiva (Idéntica a frame_ruta_breadcrumb_tk en la App de Escritorio)
    if sub_k:
        b1, b2, b3, b4, b5, b6 = st.columns([0.9, 0.9, 1.8, 2.3, 2.3, 3.2])
    else:
        b1, b2, b3, b4, b6 = st.columns([1.0, 1.0, 2.0, 2.8, 4.2])
        b5 = None

    with b1:
        if st.button("◀ Ant.", use_container_width=True):
            ir_a_pantalla("vista_analitica", ecopulse.ORDEN_CLAVES_VISTAS[(idx_v - 1) % len(ecopulse.ORDEN_CLAVES_VISTAS)])
            st.rerun()
    with b2:
        if st.button("Sig. ▶", use_container_width=True):
            ir_a_pantalla("vista_analitica", ecopulse.ORDEN_CLAVES_VISTAS[(idx_v + 1) % len(ecopulse.ORDEN_CLAVES_VISTAS)])
            st.rerun()
    with b3:
        if st.button("🏠 Menú Principal", key="bc_home", use_container_width=True):
            ir_a_pantalla("menu_categorias")
            st.rerun()
    with b4:
        if st.button(f"{info_r['categoria_icono']} {info_r['categoria_titulo']}", key="bc_cat", use_container_width=True):
            navegar_a_destino(cat_k)
            st.rerun()
    if b5 is not None and sub_k:
        with b5:
            if st.button(f"{info_r['subcategoria_icono']} {info_r['subcategoria_titulo']}", key="bc_sub", use_container_width=True):
                ir_a_pantalla(sub_k)
                st.rerun()
    with b6:
        st.markdown(
            f'<div style="background:#FEF3C7; color:#0F172A; padding:7px 12px; border-radius:6px; font-weight:800; font-size:0.84rem; text-align:center;">📍 {info_r["vista_corto"]} ({idx_v + 1}/{len(ecopulse.ORDEN_CLAVES_VISTAS)})</div>',
            unsafe_allow_html=True,
        )

    # Controles rápidos contextuales según la categoría de la vista abierta
    if clave_v in ecopulse.CLAVES_VISTAS_MACRO_INDIVIDUALES:
        cf1, cf2, cf3 = st.columns([3, 3, 6])
        with cf1:
            modo_sel = st.radio(
                "Medición:",
                ["yoy", "nivel"],
                index=0 if ecopulse.ESTADO_FILTROS_MACRO_BOTONES.get("modo", "yoy") == "yoy" else 1,
                format_func=lambda x: "Var. % a/a" if x == "yoy" else "Nivel / Índice",
                horizontal=True,
            )
            ecopulse.ESTADO_FILTROS_MACRO_BOTONES["modo"] = modo_sel
        with cf2:
            vent_opts = ["3A", "5A", "10A", "20A", "MAX"]
            vent_act = str(ecopulse.ESTADO_FILTROS_MACRO_BOTONES.get("ventana", "10A")).upper()
            vent_sel = st.selectbox("Ventana Temporal:", vent_opts, index=vent_opts.index(vent_act) if vent_act in vent_opts else 2)
            ecopulse.ESTADO_FILTROS_MACRO_BOTONES["ventana"] = vent_sel

        fig_v = plt.figure(figsize=(15.2, 8.3), dpi=115)
        ecopulse.dibujar_vista_macro_individual(datos_macro, clave_vista=clave_v, modo=modo_sel, fig=fig_v)
        _mostrar_figura_mpl(fig_v)

    elif clave_v in ecopulse.MAPA_CLAVE_VISTA_A_ACTIVO_YF:
        cc1, cc2 = st.columns(2)
        with cc1:
            iv_s = st.selectbox("🕯️ Intervalo de Vela Japonesa:", [c for c, _, _ in ecopulse.OPCIONES_INTERVALO_VELA_YF], index=2)
            ecopulse.ESTADO_FILTROS_COTIZACIONES_YF["intervalo_vela"] = iv_s
        with cc2:
            nv_s = st.selectbox("🔍 Ventana (N° de Velas):", [n for n, _ in ecopulse.OPCIONES_VENTANA_VELAS_YF], index=1, format_func=lambda n: "Todas las velas" if n == 0 else f"{n} velas")
            ecopulse.ESTADO_FILTROS_COTIZACIONES_YF["num_velas"] = int(nv_s)

        col_act = ecopulse.MAPA_CLAVE_VISTA_A_ACTIVO_YF[clave_v]
        num_v = str(ecopulse.MAPA_VISTAS_MACRO.get(clave_v, {}).get("numero", "74"))
        fig_v = plt.figure(figsize=(15.2, 8.3), dpi=115)
        ecopulse.dibujar_vista_cotizacion_individual_yf(datos_macro, columna_activo=col_act, numero_vista=num_v, modo="nivel", fig=fig_v)
        _mostrar_figura_mpl(fig_v)

    elif clave_v in ecopulse.CLAVES_VISTAS_PROYECCIONES:
        cp1, cp2, cp3 = st.columns(3)
        with cp1:
            corte_s = st.selectbox(
                "🔮 Corte Muestral COVID:",
                [c for c, _, _ in ecopulse.OPCIONES_CORTE_COVID_SARIMAX],
                format_func=lambda c: dict((k, etq) for k, etq, _ in ecopulse.OPCIONES_CORTE_COVID_SARIMAX).get(c, c),
            )
            ecopulse.ESTADO_FILTROS_PROYECCION_SARIMAX["corte_muestral"] = corte_s
        with cp2:
            mod_s = st.selectbox("Especificación SARIMAX:", [m[0] for m in getattr(ecopulse, 'OPCIONES_MODELOS_CANDIDATOS_SARIMAX', [('SARIMAX(0,1,1)(0,1,1)_12', '(0,1,1)(0,1,1)12 Airline')])])
            ecopulse.ESTADO_FILTROS_PROYECCION_SARIMAX["modelo_etiqueta"] = mod_s
        with cp3:
            unid_s = st.selectbox(
                "Unidad / Escala PIB:",
                ["tco_2018", "yoy_pct", "usd_corriente", "backtest", "tabla"],
                format_func=lambda u: {"tco_2018": "Base 2018 (USD Const.)", "yoy_pct": "Var. % a/a", "usd_corriente": "USD Corrientes", "backtest": "Backtest -1 Año", "tabla": "Histórico"}.get(u, u),
            )
            ecopulse.ESTADO_FILTROS_PROYECCION_SARIMAX["escala_pib_usd"] = unid_s

        fig_v = plt.figure(figsize=(15.5, 8.6), dpi=115)
        if clave_v == "proy_imacec_pulso_yoy":
            ecopulse.dibujar_vista_proyeccion_pulso_imacec_yoy(datos_macro, fig=fig_v)
        elif clave_v == "proy_imacec_nm_sarimax":
            ecopulse.dibujar_vista_proyeccion_sarimax_imacec_no_minero(datos_macro, fig=fig_v)
        elif clave_v == "proy_imacec_nm_pulso_yoy":
            ecopulse.dibujar_vista_proyeccion_pulso_imacec_no_minero_yoy(datos_macro, fig=fig_v)
        elif clave_v == "proy_pib_anual_usd":
            ecopulse.dibujar_vista_proyeccion_pib_anual_usd(datos_macro, fig=fig_v)
        elif clave_v == "proy_instituciones_4_principales":
            ecopulse.dibujar_vista_4_principales_proyecciones_evolucion(datos_macro, fig=fig_v)
        elif clave_v == "proy_resumen_mi_proyeccion_vs_otras":
            ecopulse.dibujar_vista_resumen_mi_proyeccion_vs_otras(datos_macro, fig=fig_v)
        else:
            ecopulse.dibujar_vista_proyeccion_sarimax_imacec(datos_macro, fig=fig_v)
        _mostrar_figura_mpl(fig_v)

    elif clave_v == "modelo_islm_mf":
        cm1, cm2, cm3, cm4 = st.columns(4)
        with cm1:
            reg_mf = st.selectbox("Régimen Cambiario:", ["flexible", "fijo"], format_func=lambda x: "TC Flexible" if x == "flexible" else "TC Fijo")
            ecopulse.ESTADO_MODELADOR_ISLM_MF["regimen"] = reg_mf
        with cm2:
            mov_mf = st.selectbox("Movilidad Capitales:", ["alta", "baja", "perfecta"], format_func=lambda x: f"Movilidad {x.capitalize()}")
            ecopulse.ESTADO_MODELADOR_ISLM_MF["movilidad"] = mov_mf
        with cm3:
            shk_mf = st.selectbox(
                "Shock Macroeconómico:",
                ["fiscal_exp", "fiscal_con", "monet_exp", "monet_con", "externo_pos", "riesgo_alza"],
                format_func=lambda s: {
                    "fiscal_exp": "Gasto Fiscal Expansivo (+ΔG)",
                    "fiscal_con": "Consolidación Fiscal (-ΔG)",
                    "monet_exp": "Impulso Monetario (+ΔM)",
                    "monet_con": "Restricción Monetaria (-ΔM)",
                    "externo_pos": "Boom Exportador (+ΔY*)",
                    "riesgo_alza": "Alza Prima por Riesgo (+Δθ)",
                }.get(s, s),
            )
        with cm4:
            int_mf = st.selectbox("Intensidad:", ["leve", "moderado", "fuerte", "extremo"], index=1)
            ecopulse.ESTADO_MODELADOR_ISLM_MF["shock"] = shk_mf
            ecopulse.ESTADO_MODELADOR_ISLM_MF["intensidad"] = int_mf
            ecopulse._sincronizar_preset_a_parametros_custom_mf(shk_mf, int_mf)

        fig_v = plt.figure(figsize=(15.5, 8.6), dpi=115)
        ecopulse.dibujar_vista_modelador_islm_mundell_fleming(datos_macro, fig=fig_v)
        _mostrar_figura_mpl(fig_v)