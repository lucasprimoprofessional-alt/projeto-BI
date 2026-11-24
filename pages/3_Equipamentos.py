"""
Página 3 — Equipamentos & Obsolescência.
Monitoramento do ciclo de vida dos ativos, parque instalado e Score Composto de Atenção.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.equipment_analysis import get_equipment_incident_ratio
from modules.obsolescence_analysis import (
    get_obsolescence_distribution,
    get_obsolescence_summary_kpis,
    calculate_top_attention_categories
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
df_inventario = st.session_state.get("raw_inventario")
active_chips = st.session_state.get("active_chips", [])

if df_inventario is None or df_inventario.empty:
    render_page_header("Equipamentos & Obsolescência", "Gestão do parque instalado e ciclo de vida.")
    render_empty_state("Inventário de equipamentos não encontrado.")
    st.stop()

colors = get_theme_colors()

# 1. Insight Automático
kpis_obs = get_obsolescence_summary_kpis(df_inventario)
top_attention = calculate_top_attention_categories(df_filtered, df_inventario)
cat_critica = top_attention.iloc[0]["Categoria"] if not top_attention.empty else "N/D"
score_critico = top_attention.iloc[0]["Score_Atencao"] if not top_attention.empty else 0.0

obs_pct_str = f"{kpis_obs['pct_obsoletos']:.1f}%".replace(".", ",")
score_str = f"{score_critico:.1f}".replace(".", ",")

insight_texto = (
    f"Atualmente, <b>{obs_pct_str}</b> do parque atingiu ou superou a vida útil estimada. "
    f"A categoria com maior índice de criticidade no Score de Atenção é <b>{cat_critica}</b> (Score: {score_str}/100)."
)

render_page_header(
    title="Equipamentos & Obsolescência",
    subtitle="Acompanhamento da saúde do patrimônio tecnológico, taxas de obsolescência e matriz de risco.",
    insight=insight_texto
)

# 2. Barra de Filtros Ativos
render_active_filter_chips(len(df_raw), len(df_filtered), active_chips)

# 3. Métricas de Topo (Sem reticências)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de ativos", format_number_br(kpis_obs["total"]))
c2.metric("Ativos obsoletos", format_number_br(kpis_obs["obsoletos"]), f"{format_percent_br(kpis_obs['pct_obsoletos'])} do parque", delta_color="inverse")
c3.metric("Próximos à obsolescência", format_number_br(kpis_obs["proximos"]), f"{format_percent_br(kpis_obs['pct_proximos'])} do parque")
c4.metric("Dentro da vida útil", format_number_br(kpis_obs["dentro_prazo"]), f"{format_percent_br(kpis_obs['pct_dentro_prazo'])} do parque")

render_section_header("Priorização Estratégica: Score Composto de Atenção")

# 4. Tabela de Priorização com Formatação Limpa
df_view_attention = top_attention.copy()
df_view_attention["Custo_Total_Estimado"] = df_view_attention["Custo_Total_Estimado"].apply(format_currency_br)
df_view_attention["Taxa_Alto_Impacto"] = df_view_attention["Taxa_Alto_Impacto"].apply(format_percent_br)
df_view_attention["Taxa_Obsolescencia"] = df_view_attention["Taxa_Obsolescencia"].apply(format_percent_br)
df_view_attention["Idade_Media"] = df_view_attention["Idade_Media"].round(1).astype(str).str.replace(".", ",") + " anos"

st.dataframe(
    df_view_attention[[
        "Categoria", "Score_Atencao", "Nivel_Prioridade", "Total_Incidentes",
        "Taxa_Alto_Impacto", "Custo_Total_Estimado", "Taxa_Obsolescencia", "Idade_Media"
    ]],
    column_config={
        "Score_Atencao": st.column_config.ProgressColumn(
            "Score de Risco",
            help="Pontuação ponderada de 0 a 100",
            format="%.1f",
            min_value=0,
            max_value=100
        ),
        "Nivel_Prioridade": st.column_config.TextColumn("Parecer de Gestão"),
        "Total_Incidentes": st.column_config.NumberColumn("Chamados"),
        "Custo_Total_Estimado": st.column_config.TextColumn("Custo Manutenção"),
        "Taxa_Obsolescencia": st.column_config.TextColumn("% Obsoletos"),
        "Idade_Media": st.column_config.TextColumn("Idade Média")
    },
    use_container_width=True,
    hide_index=True
)

with st.expander("Entenda o cálculo do Score de Atenção", expanded=False):
    st.markdown("""
    Para não julgar uma categoria apenas pelo volume absoluto de chamados, o modelo aplica uma ponderação multicritério:
    * **Volume de Incidentes:** 30%
    * **Ocorrências de Alto Impacto:** 25%
    * **Custo Total Estimado de Reparo:** 25%
    * **Taxa de Equipamentos Obsoletos:** 20%
    """)

render_section_header("Diagnóstico de Obsolescência e Parque Instalado")

# 5. Gráficos Comparativos
col_g1, col_g2 = st.columns(2)

with col_g1:
    obs_dist = get_obsolescence_distribution(df_inventario)
    fig_obs = px.bar(
        obs_dist,
        x="Categoria",
        y="Quantidade",
        color="Ciclo_Vida",
        barmode="stack",
        color_discrete_map={
            "Obsoleto / Vencido": colors["danger"],
            "Próximo à Obsolescência": colors["warning"],
            "Dentro da Vida Útil": colors["success"]
        }
    )
    fig_obs = apply_plotly_theme(fig_obs, height=310, title="Distribuição do Ciclo de Vida por Categoria", show_legend=True)
    st.plotly_chart(fig_obs, use_container_width=True)

with col_g2:
    ratio_df = get_equipment_incident_ratio(df_filtered, df_inventario)
    fig_ratio = px.bar(
        ratio_df,
        x="Categoria",
        y="Incidentes_Por_Equipamento",
        text="Incidentes_Por_Equipamento",
        color_discrete_sequence=[colors["primary"]]
    )
    fig_ratio.update_traces(texttemplate="%{y:.2f} chamados/ativo", textposition="outside")
    fig_ratio = apply_plotly_theme(fig_ratio, height=310, title="Índice de Falhas por Ativo Instalado")
    st.plotly_chart(fig_ratio, use_container_width=True)
