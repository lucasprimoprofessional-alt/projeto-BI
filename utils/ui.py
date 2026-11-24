"""
Componentes visuais e padronização de interface (UI) — BI Energisa Paraíba.
Design minimalista, contraste WCAG AA e conforto visual para executivos.
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
import streamlit as st
import plotly.graph_objects as go
from utils.helpers import format_number_br, format_percent_br

BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"

def get_theme_colors() -> Dict[str, str]:
    """Retorna as cores corporativas padronizadas da aplicação com alto contraste."""
    return {
        "primary": "#005596",        # Azul Energisa Oficial
        "primary_light": "#0083CA",  # Azul Claro
        "accent": "#FF7A00",         # Laranja Sóbrio
        "neutral_dark": "#0F172A",   # Texto Primário (Slate 900)
        "neutral_mid": "#334155",    # Texto Secundário (Slate 700 - Contraste 8.5:1)
        "neutral_muted": "#475569",  # Rótulos de KPI (Slate 600 - Contraste 6.8:1)
        "neutral_light": "#F8FAFC",  # Slate 50
        "border": "#CBD5E1",         # Slate 300
        "card_bg": "#FFFFFF",
        "danger": "#DC2626",         # Vermelho semântico
        "warning": "#D97706",        # Âmbar semântico
        "success": "#16A34A"         # Verde semântico
    }

def inject_custom_css():
    """Injeta a folha de estilos CSS da aplicação."""
    css_file = ASSETS_DIR / "style.css"
    if css_file.exists():
        with open(css_file, "r", encoding="utf-8") as f:
            css = f.read()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

def render_page_header(title: str, subtitle: str, insight: Optional[str] = None):
    """
    Renderiza cabeçalho executivo limpo.
    O insight é renderizado como um parágrafo contínuo único, evitando separação de palavras.
    """
    st.markdown(f"""
    <div class="page-header-container">
        <h1 class="page-header-title">{title}</h1>
        <p class="page-header-subtitle">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

    if insight:
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-label-row">
                <span class="insight-pill">DESTAQUE ANALÍTICO</span>
            </div>
            <p class="insight-paragraph">{insight}</p>
        </div>
        """, unsafe_allow_html=True)

def render_section_header(title: str, description: Optional[str] = None):
    """Título de seção com contraste e espaçamento harmônico."""
    st.markdown(f"""
    <div style="margin-top: 1.5rem; margin-bottom: 0.75rem;">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #005596; margin: 0;">{title}</h3>
        {f'<p style="font-size: 0.85rem; color: #475569; margin: 3px 0 0 0;">{description}</p>' if description else ''}
    </div>
    """, unsafe_allow_html=True)

def apply_plotly_theme(
    fig: go.Figure,
    height: int = 320,
    title: Optional[str] = None,
    barmode: Optional[str] = None,
    show_legend: bool = False
) -> go.Figure:
    """Padroniza gráficos Plotly com alto contraste e sem linhas pesadas de fundo."""
    colors = get_theme_colors()

    fig.update_layout(
        template="plotly_white",
        height=height,
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=14, color=colors["neutral_dark"], family="-apple-system, sans-serif"),
            x=0.0,
            xanchor="left",
            y=0.98
        ) if title else None,
        font=dict(family="-apple-system, sans-serif", size=12, color=colors["neutral_mid"]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40 if title else 20, b=30, l=40, r=20),
        showlegend=show_legend,
        barmode=barmode,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            title=None,
            font=dict(size=11, color=colors["neutral_mid"])
        )
    )

    fig.update_xaxes(
        showgrid=False,
        linecolor=colors["border"],
        linewidth=1,
        tickfont=dict(size=11, color=colors["neutral_dark"])
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#E2E8F0",
        gridwidth=1,
        linecolor=colors["border"],
        linewidth=1,
        tickfont=dict(size=11, color=colors["neutral_dark"])
    )

    return fig

def render_active_filter_chips(total_rows: int, filtered_rows: int, active_filters: List[Dict[str, str]]):
    """Exibe barra de status no topo: contador 'X de Y' e chips removíveis."""
    pct = (filtered_rows / total_rows * 100) if total_rows > 0 else 0
    
    col_info, col_btn = st.columns([5, 1])
    with col_info:
        chips_html = "".join([
            f'<span class="filter-chip filter-chip-accent" style="margin-right: 6px;"><b>{f["label"]}:</b> {f["value"]}</span>'
            for f in active_filters
        ])
        
        st.markdown(f"""
        <div class="filter-bar-container">
            <span class="filter-bar-counter">Exibindo {format_number_br(filtered_rows)} de {format_number_br(total_rows)} chamados ({format_percent_br(pct)})</span>
            {chips_html if active_filters else '<span class="filter-chip">Nenhum filtro ativo (Base total)</span>'}
        </div>
        """, unsafe_allow_html=True)
        
    with col_btn:
        if active_filters:
            if st.button("Limpar filtros", key="btn_clear_top", use_container_width=True):
                from utils.filters import reset_filters
                reset_filters()
                st.rerun()

def render_empty_state(message: str = "Nenhum chamado encontrado para os filtros selecionados."):
    """Exibe estado vazio acolhedor quando os filtros não retornam dados."""
    st.markdown(f"""
    <div class="empty-state-box">
        <div class="empty-state-title">Sem resultados para a seleção</div>
        <div class="empty-state-desc">{message}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Restaurar todos os filtros", key="empty_state_reset"):
        from utils.filters import reset_filters
        reset_filters()
        st.rerun()
