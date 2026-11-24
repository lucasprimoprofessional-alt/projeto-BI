"""
Página 1 — Visão Executiva.
Panorama macro consolidado para o Gerente de TI da Energisa Paraíba.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.incident_analysis import get_general_incident_kpis, get_incidents_temporal_series
from modules.equipment_analysis import get_equipment_park_distribution
from modules.cost_analysis import get_cost_kpis
from utils.helpers import format_number_br, format_currency_br, format_currency_compact, format_percent_br
from utils.ui import (
    render_page_header,
    render_section_header,
    render_active_filter_chips,
    render_empty_state,
    apply_plotly_theme,
    get_theme_colors
)

# 1. Recuperação do estado
df_filtered = st.session_state.get("filtered_df")
df_raw = st.session_state.get("raw_chamados")
df_inventario = st.session_state.get("raw_inventario")
active_chips = st.session_state.get("active_chips", [])

if df_filtered is None or df_filtered.empty:
    render_page_header("Visão Executiva", "Panorama consolidado dos ativos e chamados de suporte técnico.")
    render_empty_state("Nenhum chamado corresponde aos filtros atuais. Tente ajustar o período ou as categorias.")
    st.stop()

# 2. Geração de Insight Automático Real
cat_counts = df_filtered["Tipo de Equipamento"].value_counts()
cat_lider = cat_counts.index[0] if not cat_counts.empty else "N/D"
pct_lider = (cat_counts.iloc[0] / len(df_filtered) * 100) if not cat_counts.empty else 0.0
custo_lider = df_filtered[df_filtered["Tipo de Equipamento"] == cat_lider]["Custo_Total_Estimado"].sum()

pct_str = f"{pct_lider:.1f}%".replace(".", ",")
insight_texto = (
    f"A categoria <b>{cat_lider}</b> lidera as demandas com <b>{pct_str}</b> dos chamados "
    f"e <b>{format_currency_br(custo_lider)}</b> em custos estimados de manutenção no período selecionado."
)

render_page_header(
    title="Visão Executiva",
    subtitle="Painel estratégico para monitoramento de disponibilidade, custos e incidentes em campo.",
    insight=insight_texto
)

# 3. Barra de Filtros Ativos
render_active_filter_chips(len(df_raw), len(df_filtered), active_chips)

# 4. KPIs Estratégicos (Rótulos objetivos e valores sem reticências)
kpis_inc = get_general_incident_kpis(df_filtered)
kpis_custo = get_cost_kpis(df_filtered)
colors = get_theme_colors()

# Linha 1: Volume & Finanças
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de chamados", format_number_br(kpis_inc["total_chamados"]))
c2.metric("Custo estimado", format_currency_compact(kpis_custo["custo_total"]), help=format_currency_br(kpis_custo["custo_total"]))
c3.metric("Taxa de resolução", format_percent_br(kpis_inc["taxa_resolucao"]))
c4.metric("Cumprimento de SLA", format_percent_br(kpis_inc["sla_cumprido_pct"]))

# Linha 2: Criticidade & Eficiência
c5, c6, c7, c8 = st.columns(4)
c5.metric("Chamados alto impacto", format_number_br(kpis_inc["alto_impacto"]), f"{format_percent_br(kpis_inc['pct_alto_impacto'])} do total")
c6.metric("Chamados pendentes", format_number_br(kpis_inc["pendentes"]))
mttr_h_str = f"{kpis_inc['mttr_horas']:.1f} h".replace(".", ",")
mttr_d_str = f"{kpis_inc['mttr_horas']/24:.1f} dias".replace(".", ",")
c7.metric("Tempo médio resolução", mttr_h_str, mttr_d_str, help=f"MTTR médio: {mttr_h_str}")
c8.metric("Custo médio / chamado", format_currency_br(kpis_custo["custo_medio_incidente"]))

render_section_header("Distribuição e Desempenho por Categoria")

# 5. Gráficos com Cross-Filtering Interativo
col_g1, col_g2 = st.columns(2)

with col_g1:
    df_cat_inc = df_filtered["Tipo de Equipamento"].value_counts().reset_index()
    df_cat_inc.columns = ["Categoria", "Total"]
    df_cat_inc = df_cat_inc.sort_values(by="Total", ascending=True)

    fig_cat = px.bar(
        df_cat_inc,
        x="Total",
        y="Categoria",
        orientation="h",
        text="Total",
        color_discrete_sequence=[colors["primary"]]
    )
    fig_cat.update_traces(textposition="outside", texttemplate="%{x:,.0f}")
    fig_cat = apply_plotly_theme(fig_cat, height=280, title="Incidentes por Categoria de Equipamento")
    
    chart_selection = st.plotly_chart(
        fig_cat,
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key="chart_select_cat_p1"
    )

    if chart_selection and chart_selection.get("selection") and chart_selection["selection"].get("points"):
        selected_point = chart_selection["selection"]["points"][0]
        selected_cat = selected_point.get("y")
        if selected_cat and st.session_state.get("cross_filter_category") != selected_cat:
            st.session_state["cross_filter_category"] = selected_cat
            st.rerun()

with col_g2:
    df_park = get_equipment_park_distribution(df_inventario)
    df_park = df_park.sort_values(by="Total_Ativos", ascending=True)

    fig_park = px.bar(
        df_park,
        x="Total_Ativos",
        y="Categoria",
        orientation="h",
        text="Total_Ativos",
        color_discrete_sequence=[colors["primary_light"]]
    )
    fig_park.update_traces(textposition="outside", texttemplate="%{x:,.0f}")
    fig_park = apply_plotly_theme(fig_park, height=280, title="Ativos no Inventário por Categoria")
    st.plotly_chart(fig_park, use_container_width=True)

render_section_header("Evolução Temporal e Severidade")

col_g3, col_g4 = st.columns([3, 2])

with col_g3:
    df_evo = get_incidents_temporal_series(df_filtered, freq="M")
    fig_evo = px.line(
        df_evo,
        x="Periodo",
        y="Quantidade",
        markers=True,
        color_discrete_sequence=[colors["primary"]]
    )
    fig_evo.update_traces(fill="tozeroy", fillcolor="rgba(0, 85, 150, 0.08)", line=dict(width=2.5))
    fig_evo = apply_plotly_theme(fig_evo, height=290, title="Evolução Mensal de Chamados")
    st.plotly_chart(fig_evo, use_container_width=True)

with col_g4:
    imp_df = df_filtered["Impacto Causado"].value_counts().reset_index()
    imp_df.columns = ["Impacto", "Quantidade"]
    fig_imp = px.pie(
        imp_df,
        names="Impacto",
        values="Quantidade",
        color="Impacto",
        color_discrete_map={
            "Alto": colors["danger"],
            "Médio": colors["warning"],
            "Baixo": colors["success"]
        },
        hole=0.60
    )
    fig_imp.update_traces(textinfo="percent+label", textposition="outside")
    fig_imp = apply_plotly_theme(fig_imp, height=290, title="Proporção de Impacto na Operação", show_legend=False)
    st.plotly_chart(fig_imp, use_container_width=True)
