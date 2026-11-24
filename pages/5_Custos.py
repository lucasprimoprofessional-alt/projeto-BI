"""
Página 5 — Custos de Manutenção.
Análise financeira estimada de peças sobressalentes, mão de obra e serviços técnicos a partir de custos.json.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.cost_analysis import (
    get_cost_kpis,
    get_costs_by_category,
    get_costs_by_model,
    get_cost_temporal
)
from utils.helpers import format_number_br, format_currency_br, format_currency_compact, format_percent_br
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
    render_page_header("Custos de Manutenção", "Detalhamento financeiro estimado de reparos e peças.")
    render_empty_state()
    st.stop()

colors = get_theme_colors()
kpis_custo = get_cost_kpis(df_filtered)

# 1. Insight Automático Real
pct_pecas = kpis_custo["pct_pecas"]
maior_peca = df_filtered[df_filtered["Custo_Peca"] > 0]["Componente_Defeito"].value_counts()
comp_lider = maior_peca.index[0] if not maior_peca.empty else "Substituições de hardware"
pct_pecas_str = f"{pct_pecas:.1f}%".replace(".", ",")

insight_texto = (
    f"A troca de componentes físicos (peças) representa <b>{pct_pecas_str}</b> do custo estimado total, "
    f"tendo <b>{comp_lider}</b> como principal elemento de despesa na manutenção."
)

render_page_header(
    title="Custos de Manutenção",
    subtitle="Projeção e controle financeiro de sobressalentes e serviços técnicos especializados.",
    insight=insight_texto
)

# 2. Nota Metodológica Transparente
st.markdown("""
<div style="font-size: 0.85rem; color: #475569; background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.5rem 0.75rem; border-radius: 6px; margin-bottom: 1rem;">
    💡 <b>Nota de Transparência:</b> A ferramenta de ITSM não registra notas fiscais ou faturamento direto. Todos os valores apresentados são <b>estimativas paramétricas</b> derivadas da tabela homologada em <code>config/custos.json</code>.
</div>
""", unsafe_allow_html=True)

# 3. Barra de Filtros Ativos
render_active_filter_chips(len(df_raw), len(df_filtered), active_chips)

# 4. KPIs Financeiros de Destaque (Sem reticências)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Custo total estimado", format_currency_compact(kpis_custo["custo_total"]), help=format_currency_br(kpis_custo["custo_total"]))
c2.metric("Gasto com peças", format_currency_compact(kpis_custo["custo_pecas"]), f"{format_percent_br(kpis_custo['pct_pecas'])} do total", help=format_currency_br(kpis_custo["custo_pecas"]))
c3.metric("Gasto com mão de obra", format_currency_compact(kpis_custo["custo_mao_obra"]), f"{format_percent_br(kpis_custo['pct_mao_obra'])} do total", help=format_currency_br(kpis_custo["custo_mao_obra"]))
c4.metric("Custo médio / chamado", format_currency_br(kpis_custo["custo_medio_incidente"]))

render_section_header("Composição e Distribuição dos Custos")

# 5. Gráficos: Custos por Categoria & Peças vs. Serviços
col_g1, col_g2 = st.columns([3, 2])

with col_g1:
    df_cat_costs = get_costs_by_category(df_filtered).sort_values(by="Custo_Total", ascending=True)
    fig_cat_cost = px.bar(
        df_cat_costs,
        x="Custo_Total",
        y="Tipo de Equipamento",
        orientation="h",
        text="Custo_Total",
        color_discrete_sequence=[colors["primary"]]
    )
    fig_cat_cost.update_traces(texttemplate="R$ %{x:,.0f}", textposition="outside")
    fig_cat_cost = apply_plotly_theme(fig_cat_cost, height=280, title="Custo Estimado por Categoria de Equipamento")
    st.plotly_chart(fig_cat_cost, use_container_width=True)

with col_g2:
    df_comp_pie = pd.DataFrame({
        "Tipo": ["Peças / Hardware", "Mão de Obra"],
        "Valor": [kpis_custo["custo_pecas"], kpis_custo["custo_mao_obra"]]
    })
    fig_pie_comp = px.pie(
        df_comp_pie,
        names="Tipo",
        values="Valor",
        color="Tipo",
        color_discrete_map={
            "Peças / Hardware": colors["primary"],
            "Mão de Obra": colors["accent"]
        },
        hole=0.60
    )
    fig_pie_comp.update_traces(textinfo="percent+label", textposition="outside")
    fig_pie_comp = apply_plotly_theme(fig_pie_comp, height=280, title="Divisão: Peças vs. Mão de Obra", show_legend=False)
    st.plotly_chart(fig_pie_comp, use_container_width=True)

render_section_header("Evolução Temporal e Maiores Ofensores Financeiros")

# 6. Evolução Temporal
df_temp_cost = get_cost_temporal(df_filtered)
fig_temp = px.bar(
    df_temp_cost,
    x="Ano_Mes_Abertura",
    y=["Custo_Pecas", "Custo_Mao_Obra"],
    labels={"value": "Custo Estimado (R$)", "Ano_Mes_Abertura": "Mês de Abertura", "variable": "Tipo de Despesa"},
    color_discrete_map={"Custo_Pecas": colors["primary"], "Custo_Mao_Obra": colors["primary_light"]}
)
fig_temp = apply_plotly_theme(fig_temp, height=290, title="Evolução Mensal dos Gastos com Reparos", barmode="stack", show_legend=True)
st.plotly_chart(fig_temp, use_container_width=True)

# 7. Tabela de Modelos Mais Dispendiosos
st.markdown("#### Ranking de Modelos com Maior Desembolso Estimado")
df_model_costs = get_costs_by_model(df_filtered, top_n=10)

df_model_view = df_model_costs.copy()
df_model_view["Custo_Total"] = df_model_view["Custo_Total"].apply(format_currency_br)
df_model_view["Custo_Medio"] = df_model_view["Custo_Medio"].apply(format_currency_br)

st.dataframe(
    df_model_view,
    column_config={
        "Tipo de Equipamento": st.column_config.TextColumn("Categoria"),
        "Modelo_Final": st.column_config.TextColumn("Modelo"),
        "Total_Incidentes": st.column_config.NumberColumn("Total de Chamados"),
        "Custo_Total": st.column_config.TextColumn("Custo Total"),
        "Custo_Medio": st.column_config.TextColumn("Custo Médio / Chamado")
    },
    use_container_width=True,
    hide_index=True
)
