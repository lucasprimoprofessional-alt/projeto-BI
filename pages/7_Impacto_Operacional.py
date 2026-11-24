"""
Página 7 — Impacto Operacional.
Avaliação de disponibilidade técnica, tempo de resolução (MTTR), cumprimento de SLA e impacto regional.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.operational_impact import (
    get_operational_kpis,
    get_impact_by_location,
    get_downtime_by_category
)
from utils.helpers import format_number_br, format_currency_br, format_percent_br
from utils.ui import (
    render_page_header,
    render_section_header,
    render_active_filter_chips,
    render_empty_state,
    apply_plotly_theme,
    get_theme_colors
)

df_filtered = st.session_state.get("filtered_df")
df_raw = st.session_state.get("raw_chamados")
active_chips = st.session_state.get("active_chips", [])

if df_filtered is None or df_filtered.empty:
    render_page_header("Impacto Operacional", "Disponibilidade e tempos de resposta.")
    render_empty_state()
    st.stop()

colors = get_theme_colors()
kpis_op = get_operational_kpis(df_filtered)

# 1. Insight Automático Real
df_loc_top = get_impact_by_location(df_filtered)
cidade_lider = df_loc_top.iloc[0]["Localidade"] if not df_loc_top.empty else "N/D"
cidade_qtd = df_loc_top.iloc[0]["Total_Chamados"] if not df_loc_top.empty else 0

mttr_str = f"{kpis_op['mttr_medio_horas']:.1f} horas".replace(".", ",")
sla_str = f"{kpis_op['taxa_sla_cumprido']:.1f}%".replace(".", ",")

insight_texto = (
    f"O tempo médio de atendimento (MTTR) é de <b>{mttr_str}</b> com "
    f"<b>{sla_str}</b> de cumprimento de SLA. O município de <b>{cidade_lider}</b> "
    f"concentra o maior volume de chamados de campo ({format_number_br(cidade_qtd)} ocorrências)."
)

render_page_header(
    title="Impacto Operacional",
    subtitle="Nível de serviço, disponibilidade tecnológica e tempos de resposta nas bases operacionais da PB.",
    insight=insight_texto
)

# 2. Nota Metodológica Discreta
st.markdown("""
<div style="font-size: 0.85rem; color: #475569; background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.5rem 0.75rem; border-radius: 6px; margin-bottom: 1rem;">
    ℹ️ <b>Diferenciação Técnica:</b> O <i>Tempo de Resolução (MTTR)</i> aqui calculado mede o ciclo de vida do ticket no sistema ITSM. A <i>Indisponibilidade Real de Campo</i> depende da existência de aparelho reserva na viatura do eletricista.
</div>
""", unsafe_allow_html=True)

# 3. Barra de Filtros Ativos
render_active_filter_chips(len(df_raw), len(df_filtered), active_chips)

# 4. KPIs Operacionais de Topo (Sem reticências)
c1, c2, c3, c4 = st.columns(4)
mttr_h_str = f"{kpis_op['mttr_medio_horas']:.1f} h".replace(".", ",")
mttr_d_str = f"{kpis_op['mttr_medio_dias']:.1f} dias".replace(".", ",")
c1.metric("Tempo médio resolução", mttr_h_str, mttr_d_str, help=f"MTTR médio: {mttr_h_str}")
c2.metric("Cumprimento de SLA", format_percent_br(kpis_op["taxa_sla_cumprido"]))
c3.metric("Chamados alto impacto", format_number_br(kpis_op["chamados_alto_impacto"]))
c4.metric("Municípios atendidos", format_number_br(kpis_op["total_localidades_atendidas"]))

render_section_header("Nível de Serviço e Eficiência por Categoria")

# 5. Gráficos: MTTR e Quebra de SLA por Categoria
col_g1, col_g2 = st.columns(2)
df_down = get_downtime_by_category(df_filtered).sort_values(by="MTTR_Medio_Horas", ascending=True)

with col_g1:
    fig_mttr = px.bar(
        df_down,
        x="MTTR_Medio_Horas",
        y="Tipo de Equipamento",
        orientation="h",
        text="MTTR_Medio_Horas",
        color_discrete_sequence=[colors["primary"]]
    )
    fig_mttr.update_traces(texttemplate="%{x:.1f} h", textposition="outside")
    fig_mttr = apply_plotly_theme(fig_mttr, height=280, title="Tempo Médio de Atendimento (Horas)")
    st.plotly_chart(fig_mttr, use_container_width=True)

with col_g2:
    df_down_sla = df_down.sort_values(by="Taxa_Quebra_SLA", ascending=True)
    fig_sla = px.bar(
        df_down_sla,
        x="Taxa_Quebra_SLA",
        y="Tipo de Equipamento",
        orientation="h",
        text="Taxa_Quebra_SLA",
        color_discrete_sequence=[colors["danger"]]
    )
    fig_sla.update_traces(texttemplate="%{x:.1f}%", textposition="outside")
    fig_sla = apply_plotly_theme(fig_sla, height=280, title="Taxa de Quebra de Prazo (Estouro de SLA)")
    st.plotly_chart(fig_sla, use_container_width=True)

render_section_header("Impacto Regional nos Municípios da Paraíba")

# 6. Distribuição Geográfica (Top 10 Municípios)
col_loc1, col_loc2 = st.columns([3, 2])

with col_loc1:
    df_loc_top10 = df_loc_top.head(10).sort_values(by="Total_Chamados", ascending=True)
    fig_loc = px.bar(
        df_loc_top10,
        x="Total_Chamados",
        y="Localidade",
        orientation="h",
        text="Total_Chamados",
        color_discrete_sequence=[colors["primary_light"]]
    )
    fig_loc.update_traces(textposition="outside", texttemplate="%{x:,.0f}")
    fig_loc = apply_plotly_theme(fig_loc, height=330, title="Top 10 Cidades com Maior Volume de Incidentes")
    st.plotly_chart(fig_loc, use_container_width=True)

with col_loc2:
    st.markdown("#### Desempenho Regional Detalhado")
    df_loc_view = df_loc_top.head(10).copy()
    df_loc_view["MTTR_Medio_Horas"] = df_loc_view["MTTR_Medio_Horas"].round(1).astype(str).str.replace(".", ",") + " h"
    df_loc_view["Custo_Total_Estimado"] = df_loc_view["Custo_Total_Estimado"].apply(format_currency_br)

    st.dataframe(
        df_loc_view[["Localidade", "Total_Chamados", "Alto_Impacto", "MTTR_Medio_Horas", "Custo_Total_Estimado"]],
        column_config={
            "Localidade": st.column_config.TextColumn("Município"),
            "Total_Chamados": st.column_config.NumberColumn("Chamados"),
            "Alto_Impacto": st.column_config.NumberColumn("Alto Impacto"),
            "MTTR_Medio_Horas": st.column_config.TextColumn("MTTR Médio"),
            "Custo_Total_Estimado": st.column_config.TextColumn("Custo Estimado")
        },
        use_container_width=True,
        hide_index=True
    )
