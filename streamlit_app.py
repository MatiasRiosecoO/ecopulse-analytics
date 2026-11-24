#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EcoPulse Analytics — Streamlit App Optimizada para Celular y Escritorio
=======================================================================
Autor: Matías Rioseco Oróstica
       Ingeniero Comercial | Magíster en Análisis Económico (c), FEN U. de Chile

Versión optimizada para Streamlit Community Cloud con soporte nativo para
dispositivos móviles (celulares) y escritorio:
  1. Adaptación automática de gráficos Matplotlib para pantalla de celular
     (reordenamiento vertical en 1 columna, tipografía ampliada y eliminación
     de barras de botones redundantes para máxima legibilidad táctil).
  2. Diseño CSS responsivo (@media max-width: 768px) con tarjetas flexibles,
     botones táctiles (44 px) y barra de navegación inferior en cada vista.
  3. Cargador insensible a mayúsculas/minúsculas (`ecopulse_analytics.py` /
     `EcoPulse_Analytics.py`) y ejecución headless (`Agg`, `--no-gui`) para Linux.
"""

from datetime import date
import importlib.util
import io
import os
from pathlib import Path
import sys
from typing import Dict, List, Optional

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
        Actualmente tu repositorio en GitHub contiene estos archivos: **`{', '.join(archivos_en_repo)}`**

        1. Ve a tu repositorio en **GitHub** ➔ haz clic en **`Add file` ➔ `Upload files`**.
        2. Sube tu archivo **`ecopulse_analytics.py`** (o **`EcoPulse_Analytics.py`**) junto a `streamlit_app.py`.
        3. Haz clic en **`Commit changes`**.
        """
    )
    archivo_subido = st.file_uploader("O sube tu `ecopulse_analytics.py` aquí para probar ahora:", type=["py"])
    if archivo_subido is not None:
        ruta_destino = Path(__file__).resolve().parent / "EcoPulse_Analytics.py"
        ruta_destino.write_bytes(archivo_subido.getvalue())
        st.success("✓ Archivo cargado correctamente. Iniciando EcoPulse Analytics...")
        st.rerun()
    st.stop()


# -----------------------------------------------------------------------------
# 2. ESTADO DE NAVEGACIÓN Y MODO CELULAR / ESCRITORIO
# -----------------------------------------------------------------------------
if "modo_oscuro" not in st.session_state:
    st.session_state["modo_oscuro"] = False
if "modo_movil" not in st.session_state:
    st.session_state["modo_movil"] = True
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
# 3. CSS RESPONSIVO (OPTIMIZADO PARA CELULAR Y ESCRITORIO)
# -----------------------------------------------------------------------------
def _aplicar_css_responsivo(oscuro: bool) -> None:
    bg_app = "#0B0F17" if oscuro else "#FAFBFD"
    bg_card = "#131C2E" if oscuro else "#FFFFFF"
    bg_subcard = "#19253A" if oscuro else "#F8FAFC"
    borde_card = "#263449" if oscuro else "#CBD5E1"
    txt_prim = "#F8FAFC" if oscuro else "#0F172A"
    txt_sec = "#CBD5E1" if oscuro else "#334155"

    st.markdown(
        f"""
        <style>
            .block-container {{
                padding-top: 0.75rem !important;
                padding-bottom: 1.5rem !important;
                padding-left: 1.1rem !important;
                padding-right: 1.1rem !important;
                max-width: 100% !important;
            }}
            .stApp {{
                background-color: {bg_app};
                color: {txt_prim};
            }}
            .ep-banner-top {{
                background: linear-gradient(90deg, #07192E 0%, #0F3D6E 100%);
                border: 2px solid #D97706;
                border-radius: 10px;
                padding: 10px 16px;
                margin-bottom: 8px;
                color: #FFFFFF;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 6px;
            }}
            .ep-barra-ruta {{
                background-color: {bg_card};
                border: 1px solid {borde_card};
                border-radius: 8px;
                padding: 8px 12px;
                margin-bottom: 8px;
                color: {txt_prim};
                font-weight: 700;
                font-size: 0.86rem;
            }}
            .ep-cat-card {{
                background-color: {bg_card};
                border: 2px solid {borde_card};
                border-radius: 10px;
                overflow: hidden;
                margin-bottom: 4px;
                min-height: 250px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}
            .ep-cat-stripe {{ height: 7px; width: 100%; }}
            .ep-cat-body {{
                padding: 11px 14px;
                flex: 1;
                display: flex;
                flex-direction: column;
            }}
            .ep-badge-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 5px;
                gap: 4px;
            }}
            .ep-badge-num {{
                color: #FFFFFF;
                font-size: 0.70rem;
                font-weight: 800;
                padding: 2px 7px;
                border-radius: 4px;
            }}
            .ep-badge-cnt {{
                font-size: 0.70rem;
                font-weight: 800;
                padding: 2px 7px;
                border-radius: 4px;
            }}
            .ep-cat-title {{
                font-size: 1.02rem;
                font-weight: 800;
                color: {txt_prim};
                margin-bottom: 2px;
            }}
            .ep-cat-sub {{
                font-size: 0.78rem;
                font-weight: 700;
                margin-bottom: 4px;
            }}
            .ep-cat-desc {{
                font-size: 0.76rem;
                color: {txt_sec};
                line-height: 1.32;
                margin-bottom: 6px;
            }}
            .ep-cat-items {{
                background-color: {bg_subcard};
                border: 1px solid {borde_card};
                border-radius: 6px;
                padding: 6px 8px;
                font-size: 0.72rem;
                color: {txt_prim};
                line-height: 1.38;
                margin-top: auto;
            }}
            div.stButton > button {{
                font-weight: 700 !important;
                border-radius: 8px !important;
                min-height: 42px !important;
                touch-action: manipulation;
            }}
            /* Tarjetas táctiles directas en Modo Celular (sin botón Abrir abajo) */
            .ep-mob-card-wrap div.stButton > button {{
                text-align: left !important;
                justify-content: flex-start !important;
                padding: 12px 14px !important;
                background-color: {bg_card} !important;
                color: {txt_prim} !important;
                border: 1.5px solid {borde_card} !important;
                border-left: 6px solid #0284C7 !important;
                border-radius: 10px !important;
                line-height: 1.38 !important;
                white-space: pre-line !important;
                min-height: 68px !important;
            }}
            .ep-mob-card-wrap div.stButton > button:hover {{
                border-color: #38BDF8 !important;
            }}
            /* Ajustes automáticos para pantalla de celular (< 768px) */
            @media (max-width: 768px) {{
                .block-container {{
                    padding-top: 0.45rem !important;
                    padding-left: 0.55rem !important;
                    padding-right: 0.55rem !important;
                }}
                .ep-banner-top {{
                    padding: 8px 12px;
                }}
                .ep-cat-card {{
                    min-height: 0 !important;
                    height: auto !important;
                }}
                .ep-cat-body {{
                    padding: 10px 11px;
                }}
                .ep-cat-title {{
                    font-size: 0.96rem;
                }}
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# -----------------------------------------------------------------------------
# 4. ADAPTADOR DE GRÁFICOS MATPLOTLIB PARA CELULAR (REORDENAMIENTO VERTICAL)
# -----------------------------------------------------------------------------
def _adaptar_figura_para_movil(fig: plt.Figure) -> None:
    """
    Convierte cualquier lámina panorámica de escritorio (2x2 o multipanel) en una
    lámina vertical de 1 columna optimizada para pantalla de celular:
      - Oculta la barra superior de botones internos de Matplotlib (ya que Streamlit
        provee controles táctiles nativos arriba del gráfico).
      - Apila los gráficos reales en 1 columna vertical con altura generosa.
      - Amplía títulos, ejes y leyendas para lectura cómoda sin hacer zoom.
    """
    ejes_datos = [ax for ax in fig.axes if ax.axison]
    if not ejes_datos:
        # Láminas 100% de tarjetas (ej. PROY-07) -> ajuste moderado sin apilar
        fig.set_size_inches(11.0, 9.2, forward=True)
        return

    # Ocultar barras de botones internos (sin ejes) en la parte superior (y0 > 0.78)
    ejes_pie = []
    for ax in list(fig.axes):
        if not ax.axison:
            pos = ax.get_position()
            if pos.y0 > 0.76:
                ax.set_visible(False)
            elif pos.y0 < 0.20 and pos.width > 0.60:
                ejes_pie.append(ax)
            else:
                # Tablas o paneles sin ejes dentro del cuerpo (ej. Tabla resumen en PROY-03)
                if len(getattr(ax, "tables", [])) > 0:
                    ejes_datos.append(ax)
                else:
                    ax.set_visible(False)

    n_panels = len(ejes_datos)
    alto_total = max(5.6, 3.7 * n_panels + 1.8)
    fig.set_size_inches(7.0, alto_total, forward=True)

    # Ajustar textos superiores (suptitle y subtítulos)
    for txt_f in list(getattr(fig, "texts", [])):
        pos_y = float(txt_f.get_position()[1]) if hasattr(txt_f, "get_position") else 0.5
        if pos_y > 0.96:
            txt_f.set_fontsize(min(float(txt_f.get_fontsize() or 11.0), 11.0))
        elif pos_y > 0.89:
            txt_f.set_fontsize(min(float(txt_f.get_fontsize() or 8.5), 8.2))

    top_y = 0.895
    bottom_y = 0.09 if ejes_pie else 0.03
    espacio_disponible = top_y - bottom_y
    gap = 0.055 if n_panels > 1 else 0.0
    alto_panel = (espacio_disponible - gap * max(0, n_panels - 1)) / max(1, n_panels)

    for idx_p, ax in enumerate(ejes_datos):
        y_top_i = top_y - idx_p * (alto_panel + gap)
        y_bot_i = y_top_i - alto_panel
        # Dejar margen izquierdo suficiente para etiquetas de eje Y
        ax.set_position([0.14, max(0.02, y_bot_i), 0.82, max(0.08, alto_panel)])
        try:
            ax.title.set_fontsize(10.5)
            ax.xaxis.label.set_fontsize(9.0)
            ax.yaxis.label.set_fontsize(9.0)
            ax.tick_params(axis="both", labelsize=8.5)
            leg = ax.get_legend()
            if leg is not None:
                for t_l in leg.get_texts():
                    t_l.set_fontsize(8.0)
            for tbl in getattr(ax, "tables", []):
                tbl.set_fontsize(7.5)
        except Exception:
            pass

    for ax_p in ejes_pie:
        ax_p.set_position([0.04, 0.01, 0.92, 0.065])
        for t_p in ax_p.texts:
            t_p.set_fontsize(7.2)


# -----------------------------------------------------------------------------
# 5. CARGA DE DATOS EN CACHÉ
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


def _mostrar_figura_mpl(fig: plt.Figure, nombre_descarga: str = "ecopulse_grafico.png") -> None:
    osc = bool(st.session_state["modo_oscuro"])
    movil = bool(st.session_state["modo_movil"])
    ecopulse.ESTADO_TEMA_Y_MODO_UI["modo_oscuro"] = osc
    if movil:
        _adaptar_figura_para_movil(fig)
    if osc:
        ecopulse._aplicar_tema_figura_mpl(fig)

    buf_png = io.BytesIO()
    fig.savefig(buf_png, format="png", dpi=145 if movil else 125, facecolor=fig.get_facecolor())
    buf_png.seek(0)
    st.pyplot(fig, use_container_width=True, clear_figure=True)
    plt.close(fig)

    st.download_button(
        label="📥 Descargar Gráfico en PNG",
        data=buf_png.getvalue(),
        file_name=nombre_descarga,
        mime="image/png",
        use_container_width=movil,
    )


resumen_cat = ecopulse.sincronizar_catalogo_y_contadores_vistas()
datos_macro = obtener_datos_macro_en_cache(forzar_online=False)
oscuro_act = bool(st.session_state["modo_oscuro"])
movil_act = bool(st.session_state["modo_movil"])
ecopulse.ESTADO_TEMA_Y_MODO_UI["modo_oscuro"] = oscuro_act
_aplicar_css_responsivo(oscuro_act)


# -----------------------------------------------------------------------------
# 6. BANNER SUPERIOR Y BARRA DE CONTROL GLOBAL
# -----------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="ep-banner-top">
        <div>
            <div style="font-size:0.78rem; color:#93C5FD; font-weight:700;">📊 {ecopulse.APP_NOMBRE}</div>
            <div style="font-size:1.08rem; font-weight:800; color:#FFFFFF;">
                {ecopulse.AUTOR_PERFIL['nombre']} — {ecopulse.AUTOR_PERFIL['titular']}
            </div>
        </div>
        <div style="font-size:0.74rem; color:#FDE68A; font-weight:600;">
            6 Categorías • 89 Vistas + 3 Calculadoras • {'📱 Vista Celular' if movil_act else '🖥️ Vista PC'}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

c_top1, c_top2, c_top3, c_top4, c_top5 = st.columns([2.0, 3.6, 1.0, 2.2, 2.2])
with c_top1:
    if st.button("🏠 Menú Principal", use_container_width=True, type="primary"):
        ir_a_pantalla("menu_categorias")
        st.rerun()
with c_top2:
    q_top = st.text_input(
        "Buscador",
        placeholder="🔍 Buscar vista o código (ACT-01, PROY-07, UF, IPC...)",
        label_visibility="collapsed",
        key="input_buscador_global",
    )
with c_top3:
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
with c_top4:
    etq_mov = "🖥️ Cambiar a Vista PC" if movil_act else "📱 Optimizar p/ Celular"
    if st.button(etq_mov, use_container_width=True):
        st.session_state["modo_movil"] = not movil_act
        st.rerun()
with c_top5:
    etq_tema_btn = "☀️ Modo Claro" if oscuro_act else "🌙 Modo Oscuro"
    if st.button(etq_tema_btn, use_container_width=True):
        st.session_state["modo_oscuro"] = not oscuro_act
        st.rerun()

if q_top.strip() and st.session_state["pantalla_activa"] != "vista_analitica":
    resultados_busq = ecopulse.buscar_vistas_en_catalogo(q_top.strip())
    if resultados_busq:
        st.markdown(f"##### 🔍 Resultados para «{q_top.strip()}» ({len(resultados_busq)}):")
        cols_res = st.columns(1 if movil_act else 3)
        for i_r, it_r in enumerate(resultados_busq[:9]):
            with cols_res[i_r % len(cols_res)]:
                if st.button(
                    f"{it_r.get('icono', '📊')} [{it_r.get('codigo', '')}] {it_r.get('corto_base', it_r.get('titulo', ''))}",
                    key=f"btn_res_q_{it_r['clave']}_{i_r}",
                    use_container_width=True,
                ):
                    navegar_a_destino(str(it_r["clave"]))
                    st.rerun()
        st.divider()


# -----------------------------------------------------------------------------
# 7. TARJETAS DE CATEGORÍA Y VISTAS
# -----------------------------------------------------------------------------
def _renderizar_tarjeta(
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
) -> None:
    if st.session_state["modo_oscuro"]:
        bg_suave_eff, fg_suave_eff = "#19253A", "#38BDF8"
    else:
        bg_suave_eff, fg_suave_eff = bg_suave, fg_suave

    items_html = "<br>".join(items_lista) if items_lista else ""
    bloque_items = f'<div class="ep-cat-items">{items_html}</div>' if items_html else ""

    with columna_st:
        if st.session_state.get("modo_movil", False):
            # En Modo Celular: la tarjeta completa es el botón táctil (sin botón "Abrir" abajo)
            st.markdown('<div class="ep-mob-card-wrap">', unsafe_allow_html=True)
            etq_movil = f"{icono}  {titulo}   [{badge_der}]\n{subtitulo}  ›"
            if st.button(etq_movil, key=key_boton, use_container_width=True):
                callback_fn()
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                f"""
                <div class="ep-cat-card">
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
# 8. ENRUTADOR DE PANTALLAS
# -----------------------------------------------------------------------------
pantalla = st.session_state["pantalla_activa"]

# === PANTALLA A: MENÚ PRINCIPAL (6 CATEGORÍAS) ===
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

    tarjetas_6_cats = [
        {
            "badge_izq": str(cat_1["numero_badge"]), "badge_der": str(cat_1["etiqueta_cantidad"]),
            "icono": "👤", "titulo": str(cat_1["titulo"]),
            "subtitulo": "Perfil Profesional y Trayectoria Académica",
            "descripcion": "Perfil profesional y académico de Matías Rioseco Oróstica (FEN U. de Chile; NODO XXI).",
            "items": ["▪ [PRES-01] Perfil y Trayectoria", "▪ Datos de Contacto Directo"],
            "color": "#D97706", "bg_s": "#FEF3C7", "fg_s": "#92400E",
            "btn": "👤  Abrir 1. Presentación ➔", "dest": "presentacion",
        },
        {
            "badge_izq": str(cat_2["numero_badge"]), "badge_der": str(cat_2["etiqueta_cantidad"]),
            "icono": "🏛️", "titulo": str(cat_2["titulo"]),
            "subtitulo": f"{n_subs_macro} Subcategorías • {n_vistas_macro} Vistas",
            "descripcion": "IMACEC, PIB, TCR, IPC, Empleo, Capital, Finanzas Públicas, Política Monetaria, Externo y PTF.",
            "items": ["▪ 1. Actividad (16) • 2. TCR (4) • 3. IPC (4)", "▪ 4. Empleo (12) • 5–9. Cap, Fis, Mon, Ext, PTF"],
            "color": "#0F3D6E", "bg_s": "#DBEAFE", "fg_s": "#1E3A8A",
            "btn": f"🏛️  Explorar {n_vistas_macro} Vistas Macro ➔", "dest": "sub_macroeconomicas",
        },
        {
            "badge_izq": str(cat_3["numero_badge"]), "badge_der": str(cat_3["etiqueta_cantidad"]),
            "icono": "💹", "titulo": str(cat_3["titulo"]),
            "subtitulo": f"Divisas, Commodities e IPSA ({n_vistas_cot} Vistas)",
            "descripcion": "Velas Japonesas (OHLC) vía Yahoo Finance: Brent, USD/CLP, Cobre, IPSA, Oro, Molibdeno, Litio y GNL.",
            "items": ["▪ [COT-01..04] Brent • USD/CLP • Cobre • IPSA", "▪ [COT-05..08] Oro • Molibdeno • Litio • GNL"],
            "color": "#0369A1", "bg_s": "#E0F2FE", "fg_s": "#0369A1",
            "btn": "💹  Explorar Cotizaciones ➔", "dest": "sub_cotizaciones",
        },
        {
            "badge_izq": str(cat_4["numero_badge"]), "badge_der": str(cat_4["etiqueta_cantidad"]),
            "icono": "🔮", "titulo": str(cat_4["titulo"]),
            "subtitulo": f"Modelos SARIMAX y Consenso ({n_vistas_proy} Vistas)",
            "descripcion": "Proyecciones SARIMAX (IMACEC, PIB Anual USD con YTD real), 4 Instituciones y Resumen en Tarjetas.",
            "items": ["▪ [PROY-01..03] IMACEC y PIB Anual USD", "▪ [PROY-06..07] Instituciones y Resumen Tarjetas"],
            "color": "#6D28D9", "bg_s": "#F3E8FF", "fg_s": "#5B21B6",
            "btn": "🔮  Explorar Proyecciones ➔", "dest": "sub_proyecciones",
        },
        {
            "badge_izq": str(cat_5["numero_badge"]), "badge_der": str(cat_5["etiqueta_cantidad"]),
            "icono": "📐", "titulo": str(cat_5["titulo"]),
            "subtitulo": "Equilibrio General IS-LM-BP (Mundell-Fleming)",
            "descripcion": "Simulador interactivo de política fiscal, monetaria y externa bajo Tipo de Cambio Flexible o Fijo.",
            "items": ["▪ [MOD-01] Curvas IS-LM-BP, UIP, I-S y NX"],
            "color": "#0F766E", "bg_s": "#CCFBF1", "fg_s": "#115E59",
            "btn": "📐  Abrir Modelador IS-LM ➔", "dest": "modelo_islm_mf",
        },
        {
            "badge_izq": str(cat_6["numero_badge"]), "badge_der": str(cat_6["etiqueta_cantidad"]),
            "icono": "🧮", "titulo": str(cat_6["titulo"]),
            "subtitulo": "Calculadoras Oficiales (INE • SII • BCCh)",
            "descripcion": "Calculadora de IPC (INE), Calculadora diaria de UF (SII 2026) y Conversor de Tipo de Cambio.",
            "items": ["▪ [CALC-01] IPC INE • [CALC-02] UF SII 2026", "▪ [CALC-03] Conversor Divisas USD/EUR/CLP/UF"],
            "color": "#0284C7", "bg_s": "#E0F2FE", "fg_s": "#0369A1",
            "btn": "🧮  Abrir Calculadoras ➔", "dest": "calculadoras_hub",
        },
    ]

    n_cols = 1 if movil_act else 3
    for i_start in range(0, len(tarjetas_6_cats), n_cols):
        cols_row = st.columns(n_cols)
        for j_c in range(n_cols):
            if i_start + j_c >= len(tarjetas_6_cats):
                break
            item_c = tarjetas_6_cats[i_start + j_c]
            dest_c = item_c["dest"]
            _renderizar_tarjeta(
                columna_st=cols_row[j_c],
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
            )


# === PANTALLA B: SUBPANTALLA DE LAS 9 SUBCATEGORÍAS MACRO ===
elif pantalla == "sub_macroeconomicas":
    if st.button("⬅ Volver a las 6 Categorías", use_container_width=movil_act):
        ir_a_pantalla("menu_categorias")
        st.rerun()

    subs_macro = ecopulse.SUBCATEGORIAS_MACROECONOMICAS
    n_cols = 1 if movil_act else 3
    for f_s in range(0, len(subs_macro), n_cols):
        cols_s = st.columns(n_cols)
        for c_s in range(n_cols):
            if f_s + c_s >= len(subs_macro):
                break
            sub_info = subs_macro[f_s + c_s]
            clv_sub = str(sub_info["clave_sub"])
            vistas_s = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("subcategoria_clave") == clv_sub]
            items_s = [f"▪ [{v['codigo']}] {v['corto_base']}" for v in vistas_s[:3]]
            _renderizar_tarjeta(
                columna_st=cols_s[c_s],
                badge_izq=f"2.{sub_info['numero']}",
                badge_der=str(sub_info["etiqueta_cantidad"]),
                icono=str(sub_info["icono"]),
                titulo=str(sub_info["titulo"]),
                subtitulo=f"{sub_info['rango_codigos']}",
                descripcion=str(sub_info["descripcion"]),
                items_lista=items_s,
                color_hex=str(sub_info["color"]),
                bg_suave="#EFF6FF",
                fg_suave=str(sub_info["color"]),
                texto_boton=f"{sub_info['icono']}  Abrir {sub_info['nombre_limpio']} ➔",
                key_boton=f"btn_sub_macro_{clv_sub}",
                callback_fn=lambda k=clv_sub: ir_a_pantalla(k),
            )


# === PANTALLA C: GRILLA DE TARJETAS DE VISTAS ===
elif pantalla in ecopulse.MAPA_SUBCATEGORIAS_MACRO or pantalla in ("sub_cotizaciones", "sub_proyecciones", "sub_modelacion", "sub_calculadoras"):
    es_sub_macro = pantalla in ecopulse.MAPA_SUBCATEGORIAS_MACRO
    if es_sub_macro:
        if st.button("⬅ Volver a las 9 Subcategorías Macro", use_container_width=movil_act):
            ir_a_pantalla("sub_macroeconomicas")
            st.rerun()
        lista_tarjetas = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("subcategoria_clave") == pantalla]
    elif pantalla == "sub_cotizaciones":
        if st.button("⬅ Volver a las 6 Categorías", use_container_width=movil_act):
            ir_a_pantalla("menu_categorias")
            st.rerun()
        lista_tarjetas = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("categoria") == "cotizaciones"]
    elif pantalla == "sub_proyecciones":
        if st.button("⬅ Volver a las 6 Categorías", use_container_width=movil_act):
            ir_a_pantalla("menu_categorias")
            st.rerun()
        lista_tarjetas = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("categoria") == "proyecciones"]
    elif pantalla == "sub_modelacion":
        if st.button("⬅ Volver a las 6 Categorías", use_container_width=movil_act):
            ir_a_pantalla("menu_categorias")
            st.rerun()
        lista_tarjetas = [v for v in ecopulse.CATALOGO_VISTAS_MACRO if v.get("categoria") == "modelacion"]
    else:
        if st.button("⬅ Volver a las 6 Categorías", use_container_width=movil_act):
            ir_a_pantalla("menu_categorias")
            st.rerun()
        lista_tarjetas = ecopulse.CATALOGO_INSTRUMENTOS_CALCULADORAS

    n_cols = 1 if movil_act else 3
    for idx_v in range(0, len(lista_tarjetas), n_cols):
        cols_v = st.columns(n_cols)
        for c_i in range(n_cols):
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
            _renderizar_tarjeta(
                columna_st=cols_v[c_i],
                badge_izq=f"CÓD: {cod_v}" if es_calc else f"{cod_v} • V{num_v}",
                badge_der="CALCULADORA" if es_calc else str(v_meta.get("codigo_global", f"V-{num_v}")),
                icono=str(v_meta.get("icono", "📊")),
                titulo=corto_v,
                subtitulo=tit_v[:85] + ("..." if len(tit_v) > 85 else ""),
                descripcion=sub_v[:150] + ("..." if len(sub_v) > 150 else ""),
                items_lista=[],
                color_hex=col_v,
                bg_suave="#E0F2FE",
                fg_suave="#0369A1",
                texto_boton=f"🧮  Abrir {corto_v} ➔" if es_calc else f"📊  Abrir Vista {num_v} [{cod_v}] ➔",
                key_boton=f"btn_card_v_{clv_dest}",
                callback_fn=(lambda k=clv_dest: ir_a_pantalla("calculadoras_hub", k)) if es_calc else (lambda k=clv_dest: ir_a_pantalla("vista_analitica", k)),
            )


# === PANTALLA D: PRESENTACIÓN PROFESIONAL ===
elif pantalla == "presentacion":
    if st.button("🏠 Volver al Menú Principal", use_container_width=movil_act):
        ir_a_pantalla("menu_categorias")
        st.rerun()
    st.markdown(f"### 👤 {ecopulse.AUTOR_PERFIL['nombre']}")
    st.info(ecopulse.AUTOR_PERFIL["resumen"])
    col_p1, col_p2 = st.columns(1 if movil_act else 2)
    with col_p1:
        st.markdown("#### 💼 Trayectoria Profesional")
        for item_exp in ecopulse.AUTOR_PERFIL.get("experiencia", []):
            if isinstance(item_exp, (tuple, list)) and len(item_exp) >= 2:
                with st.expander(f"**{item_exp[0]}**", expanded=True):
                    st.write(item_exp[1])
            else:
                st.markdown(f"- {item_exp}")
    with col_p2:
        st.markdown("#### 🎓 Formación Académica")
        for item_form in ecopulse.AUTOR_PERFIL.get("formacion", []):
            st.markdown(f"🎓 **{item_form}**")


# === PANTALLA E: SUITE DE 3 CALCULADORAS OFICIALES ===
elif pantalla == "calculadoras_hub":
    c_cb1, c_cb2, c_cb3, c_cb4 = st.columns(4 if not movil_act else 2)
    with c_cb1:
        if st.button("🏠 Menú", key="calc_home_btn", use_container_width=True):
            ir_a_pantalla("menu_categorias")
            st.rerun()
    with c_cb2:
        if st.button("📈 IPC (INE)", type="primary" if st.session_state["calculadora_activa"] == "calc_ipc" else "secondary", use_container_width=True):
            st.session_state["calculadora_activa"] = "calc_ipc"
            st.rerun()
    with c_cb3:
        if st.button("🏦 UF (SII 2026)", type="primary" if st.session_state["calculadora_activa"] == "calc_uf" else "secondary", use_container_width=True):
            st.session_state["calculadora_activa"] = "calc_uf"
            st.rerun()
    with c_cb4:
        if st.button("💱 Tipo de Cambio", type="primary" if st.session_state["calculadora_activa"] == "calc_tipo_cambio" else "secondary", use_container_width=True):
            st.session_state["calculadora_activa"] = "calc_tipo_cambio"
            st.rerun()

    serie_ipc_ine = ecopulse._construir_serie_ipc_empalmada_ine()
    meses_nombres = ecopulse.NOMBRES_MESES_ES
    calc_act = st.session_state["calculadora_activa"]

    if calc_act == "calc_ipc":
        st.markdown("#### 📈 Calculadora de IPC (Modelo Oficial INE)")
        c_i1, c_i2 = st.columns(2)
        with c_i1:
            m_ini_nom = st.selectbox("Mes Inicio:", meses_nombres, index=8)
        with c_i2:
            anios_l = list(range(2026, 1989, -1))
            a_ini = st.selectbox("Año Inicio:", anios_l, index=1)
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            m_fin_nom = st.selectbox("Mes Término:", meses_nombres, index=8)
        with c_f2:
            a_fin = st.selectbox("Año Término:", anios_l, index=0)
        monto_ipc_in = st.number_input("Valor a Ajustar ($ CLP):", min_value=0.0, value=1000000.0, step=50000.0, format="%.0f")

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
        var_1d = round((factor_12d - 1.0) * 100.0, 1)
        monto_ajustado = round(monto_ipc_in * factor_12d)
        dif_pesos = monto_ajustado - round(monto_ipc_in)

        k1, k2, k3 = st.columns(3 if not movil_act else 1)
        k1.metric("Valor Ajustado ($ CLP)", f"$ {_fmt_clp(monto_ajustado, 0)}", f"{'+' if dif_pesos >= 0 else '-'}$ {_fmt_clp(abs(dif_pesos), 0)}")
        k2.metric("Variación Oficial (INE)", f"{var_1d:+.1f} %".replace(".", ","), f"{m_ini_nom[:3]} {a_ini} ➔ {m_fin_nom[:3]} {a_fin}")
        k3.metric("Factor (12 decimales)", f"{factor_12d:.6f}".replace(".", ","), f"{ipc_0:.2f} ➔ {ipc_1:.2f} pts")

    elif calc_act == "calc_uf":
        st.markdown("#### 🏦 Calculadora de UF (Valores Oficiales SII 2026)")
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
        st.success(f"**1 UF Oficial SII ({d_uf:02d}/{m_uf:02d}/{a_uf}) = $ {_fmt_clp(uf_dia_val, 2)} CLP**")

        modo_uf_st = st.radio("Conversión:", ["UF_A_CLP", "CLP_A_UF"], format_func=lambda m: "UF ➔ Pesos ($)" if m == "UF_A_CLP" else "Pesos ($) ➔ UF", horizontal=True)
        monto_uf_st = st.number_input("Monto:", min_value=0.0, value=100.0 if modo_uf_st == "UF_A_CLP" else 1000000.0, step=10.0)
        if modo_uf_st == "UF_A_CLP":
            st.metric("Total en Pesos ($ CLP)", f"$ {_fmt_clp(monto_uf_st * uf_dia_val, 2)} CLP", f"Redondeado: $ {_fmt_clp(round(monto_uf_st * uf_dia_val), 0)} CLP")
        else:
            res_uf = monto_uf_st / uf_dia_val if uf_dia_val > 0 else 0.0
            st.metric("Equivalencia en UF", f"{_fmt_clp(res_uf, 2)} UF", f"Exacta: {_fmt_clp(res_uf, 6)} UF")

    else:
        st.markdown("#### 💱 Calculadora de Tipo de Cambio (SII / BCCh)")
        monedas_tc = [
            ("USD", "🇺🇸 USD — Dólar", 948.50),
            ("CLP", "🇨🇱 CLP — Peso", 1.0),
            ("EUR", "🇪🇺 EUR — Euro", 1035.80),
            ("UF",  "🏦 UF — Fomento", 41268.88),
            ("UTM", "🏛️ UTM — Tributaria", 72440.0),
            ("BRL", "🇧🇷 BRL — Real", 172.90),
        ]
        mapa_clp = {c: v for c, _, v in monedas_tc}
        etq_tc = {c: e for c, e, _ in monedas_tc}
        monto_tc = st.number_input("Monto:", min_value=0.0, value=1000.0, step=100.0)
        ct1, ct2 = st.columns(2)
        with ct1:
            c_o = st.selectbox("De:", [c for c, _, _ in monedas_tc], index=0, format_func=lambda c: etq_tc[c])
        with ct2:
            c_d = st.selectbox("A:", [c for c, _, _ in monedas_tc], index=1, format_func=lambda c: etq_tc[c])
        en_clp = monto_tc * mapa_clp[c_o]
        res_tc = en_clp / mapa_clp[c_d]
        st.metric(f"Resultado ({c_o} ➔ {c_d})", f"{'$ ' if c_d == 'CLP' else ''}{_fmt_clp(res_tc, 0 if c_d == 'CLP' else 2)} {c_d}")


# === PANTALLA F: VISTA ANALÍTICA (OPTIMIZADA PARA CELULAR O ESCRITORIO) ===
else:
    clave_v = st.session_state["vista_actual"]
    if clave_v not in ecopulse.ORDEN_CLAVES_VISTAS:
        clave_v = ecopulse.ORDEN_CLAVES_VISTAS[0]
        st.session_state["vista_actual"] = clave_v

    idx_v = ecopulse.ORDEN_CLAVES_VISTAS.index(clave_v)
    info_r = ecopulse.obtener_ruta_navegacion_vista(clave_v)
    cat_k = info_r["categoria_clave"]
    sub_k = info_r["subcategoria_clave"]

    # Barra superior de navegación táctil
    b1, b2, b3, b4 = st.columns(4 if not movil_act else 2)
    with b1:
        if st.button("◀ Anterior", key="top_prev", use_container_width=True):
            ir_a_pantalla("vista_analitica", ecopulse.ORDEN_CLAVES_VISTAS[(idx_v - 1) % len(ecopulse.ORDEN_CLAVES_VISTAS)])
            st.rerun()
    with b2:
        if st.button("Siguiente ▶", key="top_next", use_container_width=True):
            ir_a_pantalla("vista_analitica", ecopulse.ORDEN_CLAVES_VISTAS[(idx_v + 1) % len(ecopulse.ORDEN_CLAVES_VISTAS)])
            st.rerun()
    with b3:
        if st.button(f"{info_r['categoria_icono']} {info_r['categoria_titulo']}", key="top_cat", use_container_width=True):
            navegar_a_destino(cat_k)
            st.rerun()
    with b4:
        if sub_k and st.button(f"{info_r['subcategoria_icono']} {info_r['subcategoria_titulo']}", key="top_sub", use_container_width=True):
            ir_a_pantalla(sub_k)
            st.rerun()

    st.markdown(
        f'<div class="ep-barra-ruta">📍 {info_r["vista_corto"]} &nbsp;({idx_v + 1}/{len(ecopulse.ORDEN_CLAVES_VISTAS)}) &nbsp;•&nbsp; {"📱 Vista Celular (1 Columna)" if movil_act else "🖥️ Vista Escritorio"}</div>',
        unsafe_allow_html=True,
    )

    if clave_v in ecopulse.CLAVES_VISTAS_MACRO_INDIVIDUALES:
        cf1, cf2 = st.columns(2)
        with cf1:
            modo_sel = st.radio(
                "Medición:",
                ["yoy", "nivel"],
                index=0 if ecopulse.ESTADO_FILTROS_MACRO_BOTONES.get("modo", "yoy") == "yoy" else 1,
                format_func=lambda x: "Var. % a/a" if x == "yoy" else "Nivel",
                horizontal=True,
            )
            ecopulse.ESTADO_FILTROS_MACRO_BOTONES["modo"] = modo_sel
        with cf2:
            vent_opts = ["3A", "5A", "10A", "20A", "MAX"]
            vent_act = str(ecopulse.ESTADO_FILTROS_MACRO_BOTONES.get("ventana", "10A")).upper()
            vent_sel = st.selectbox("Ventana:", vent_opts, index=vent_opts.index(vent_act) if vent_act in vent_opts else 2)
            ecopulse.ESTADO_FILTROS_MACRO_BOTONES["ventana"] = vent_sel

        fig_v = plt.figure(figsize=(15.2, 8.3), dpi=120)
        ecopulse.dibujar_vista_macro_individual(datos_macro, clave_vista=clave_v, modo=modo_sel, fig=fig_v)
        _mostrar_figura_mpl(fig_v, f"{clave_v}.png")

    elif clave_v in ecopulse.MAPA_CLAVE_VISTA_A_ACTIVO_YF:
        cc1, cc2 = st.columns(2)
        with cc1:
            iv_s = st.selectbox("🕯️ Vela:", [c for c, _, _ in ecopulse.OPCIONES_INTERVALO_VELA_YF], index=2)
            ecopulse.ESTADO_FILTROS_COTIZACIONES_YF["intervalo_vela"] = iv_s
        with cc2:
            nv_s = st.selectbox("🔍 Velas:", [n for n, _ in ecopulse.OPCIONES_VENTANA_VELAS_YF], index=1, format_func=lambda n: "Todas" if n == 0 else f"{n} velas")
            ecopulse.ESTADO_FILTROS_COTIZACIONES_YF["num_velas"] = int(nv_s)

        col_act = ecopulse.MAPA_CLAVE_VISTA_A_ACTIVO_YF[clave_v]
        num_v = str(ecopulse.MAPA_VISTAS_MACRO.get(clave_v, {}).get("numero", "74"))
        fig_v = plt.figure(figsize=(15.2, 8.3), dpi=120)
        ecopulse.dibujar_vista_cotizacion_individual_yf(datos_macro, columna_activo=col_act, numero_vista=num_v, modo="nivel", fig=fig_v)
        _mostrar_figura_mpl(fig_v, f"{clave_v}.png")

    elif clave_v in ecopulse.CLAVES_VISTAS_PROYECCIONES:
        cp1, cp2, cp3 = st.columns(3 if not movil_act else 1)
        with cp1:
            corte_s = st.selectbox(
                "🔮 Corte COVID:",
                [c for c, _, _ in ecopulse.OPCIONES_CORTE_COVID_SARIMAX],
                format_func=lambda c: dict((k, etq) for k, etq, _ in ecopulse.OPCIONES_CORTE_COVID_SARIMAX).get(c, c),
            )
            ecopulse.ESTADO_FILTROS_PROYECCION_SARIMAX["corte_muestral"] = corte_s
        with cp2:
            mod_s = st.selectbox("Modelo SARIMAX:", [m[0] for m in getattr(ecopulse, "OPCIONES_MODELOS_CANDIDATOS_SARIMAX", [("SARIMAX(0,1,1)(0,1,1)_12", "Airline")])])
            ecopulse.ESTADO_FILTROS_PROYECCION_SARIMAX["modelo_etiqueta"] = mod_s
        with cp3:
            unid_s = st.selectbox(
                "Escala PIB:",
                ["tco_2018", "yoy_pct", "usd_corriente", "backtest", "tabla"],
                format_func=lambda u: {"tco_2018": "Base 2018", "yoy_pct": "Var. % a/a", "usd_corriente": "USD Corr.", "backtest": "Backtest -1A", "tabla": "Histórico"}.get(u, u),
            )
            ecopulse.ESTADO_FILTROS_PROYECCION_SARIMAX["escala_pib_usd"] = unid_s

        fig_v = plt.figure(figsize=(15.5, 8.6), dpi=120)
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
        _mostrar_figura_mpl(fig_v, f"{clave_v}.png")

    elif clave_v == "modelo_islm_mf":
        cm1, cm2, cm3, cm4 = st.columns(4 if not movil_act else 2)
        with cm1:
            reg_mf = st.selectbox("Régimen:", ["flexible", "fijo"], format_func=lambda x: "TC Flexible" if x == "flexible" else "TC Fijo")
            ecopulse.ESTADO_MODELADOR_ISLM_MF["regimen"] = reg_mf
        with cm2:
            mov_mf = st.selectbox("Capitales:", ["alta", "baja", "perfecta"], format_func=lambda x: f"Mov. {x.capitalize()}")
            ecopulse.ESTADO_MODELADOR_ISLM_MF["movilidad"] = mov_mf
        with cm3:
            shk_mf = st.selectbox(
                "Shock:",
                ["fiscal_exp", "fiscal_con", "monet_exp", "monet_con", "externo_pos", "riesgo_alza"],
                format_func=lambda s: {
                    "fiscal_exp": "Fiscal (+ΔG)", "fiscal_con": "Fiscal (-ΔG)",
                    "monet_exp": "Monetario (+ΔM)", "monet_con": "Monetario (-ΔM)",
                    "externo_pos": "Exportador (+ΔY*)", "riesgo_alza": "Riesgo (+Δθ)",
                }.get(s, s),
            )
        with cm4:
            int_mf = st.selectbox("Intensidad:", ["leve", "moderado", "fuerte", "extremo"], index=1)
            ecopulse.ESTADO_MODELADOR_ISLM_MF["shock"] = shk_mf
            ecopulse.ESTADO_MODELADOR_ISLM_MF["intensidad"] = int_mf
            ecopulse._sincronizar_preset_a_parametros_custom_mf(shk_mf, int_mf)

        fig_v = plt.figure(figsize=(15.5, 8.6), dpi=120)
        ecopulse.dibujar_vista_modelador_islm_mundell_fleming(datos_macro, fig=fig_v)
        _mostrar_figura_mpl(fig_v, "modelo_islm_mf.png")

    # Barra inferior táctil en celular para cambiar de vista sin subir
    st.divider()
    nb1, nb2, nb3 = st.columns(3)
    with nb1:
        if st.button("◀ Anterior", key="bot_prev", use_container_width=True):
            ir_a_pantalla("vista_analitica", ecopulse.ORDEN_CLAVES_VISTAS[(idx_v - 1) % len(ecopulse.ORDEN_CLAVES_VISTAS)])
            st.rerun()
    with nb2:
        if st.button("🏠 Menú", key="bot_home", use_container_width=True):
            ir_a_pantalla("menu_categorias")
            st.rerun()
    with nb3:
        if st.button("Siguiente ▶", key="bot_next", use_container_width=True):
            ir_a_pantalla("vista_analitica", ecopulse.ORDEN_CLAVES_VISTAS[(idx_v + 1) % len(ecopulse.ORDEN_CLAVES_VISTAS)])
            st.rerun()