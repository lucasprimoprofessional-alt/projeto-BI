"""
Página 2 — Incidentes.
Diagnóstico detalhado de sintomas, causas-raiz e comparativos temporais interativos.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from modules.incident_analysis import (
    get_incidents_by_category_and_sub,
    compare_annual,
    compare_monthly,
    compare_daily
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
    render_page_header("Incidentes", "Análise de padrões de falha e comparativos temporais.")
    render_empty_state()
    st.stop()

colors = get_theme_colors()

# 1. Insight Automático Real
subcat_top = df_filtered["Subcategoria"].value_counts()
sub_lider = subcat_top.index[0] if not subcat_top.empty else "N/D"
sub_lider_pct = (subcat_top.iloc[0] / len(df_filtered) * 100) if not subcat_top.empty else 0.0

prio_crit = ((df_filtered["Nível de Prioridade"] == "Crítico") | (df_filtered["Nível de Prioridade"] == "Alto")).sum()
prio_crit_pct = (prio_crit / len(df_filtered) * 100)

sub_pct_str = f"{sub_lider_pct:.1f}%".replace(".", ",")
crit_pct_str = f"{prio_crit_pct:.1f}%".replace(".", ",")

insight_texto = (
    f"O defeito mais recorrente é <b>{sub_lider}</b> ({sub_pct_str} das queixas). "
    f"Chamados classificados como Crítico ou Alto somam <b>{format_number_br(prio_crit)} ({crit_pct_str})</b> do total."
)

render_page_header(
    title="Incidentes",
    subtitle="Diagnóstico de causas-raiz, tipos de falha e evolução temporal das ocorrências.",
    insight=insight_texto
)

# 2. Barra de Filtros Ativos
render_active_filter_chips(len(df_raw), len(df_filtered), active_chips)

# 3. Métricas de Topo (Sem reticências)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de ocorrências", format_number_br(len(df_filtered)))
c2.metric("Principal sintoma", sub_lider, f"{sub_pct_str} dos chamados")
c3.metric("Severidade crítica/alta", format_number_br(prio_crit), f"{crit_pct_str} do total")
c4.metric("Escalonamento L2/L3", format_number_br((df_filtered["Nível de Escalonamento"] != "1° Escalonamento").sum()))

st.markdown("")

# 4. Alternador de Visão de Gráfico (Segmented Control)
view_mode = st.segmented_control(
    "Visualizar gráfico por:",
    options=["Quantidade de Chamados", "Custo Estimado (R$)"],
    default="Quantidade de Chamados"
)

col_g1, col_g2 = st.columns([3, 2])

with col_g1:
    if view_mode == "Custo Estimado (R$)":
        sub_agg = df_filtered.groupby("Subcategoria")["Custo_Total_Estimado"].sum().reset_index()
        sub_agg.columns = ["Subcategoria", "Valor"]
        sub_agg = sub_agg.sort_values(by="Valor", ascending=True)
        fig_sub = px.bar(
            sub_agg,
            x="Valor",
            y="Subcategoria",
            orientation="h",
            text="Valor",
            color_discrete_sequence=[colors["primary"]]
        )
        fig_sub.update_traces(texttemplate="R$ %{x:,.0f}", textposition="outside")
        fig_sub = apply_plotly_theme(fig_sub, height=320, title="Custo Estimado por Subcategoria de Incidente")
    else:
        sub_agg = df_filtered["Subcategoria"].value_counts().reset_index()
        sub_agg.columns = ["Subcategoria", "Valor"]
        sub_agg = sub_agg.sort_values(by="Valor", ascending=True)
        fig_sub = px.bar(
            sub_agg,
            x="Valor",
            y="Subcategoria",
            orientation="h",
            text="Valor",
            color_discrete_sequence=[colors["primary"]]
        )
        fig_sub.update_traces(texttemplate="%{x:,.0f}", textposition="outside")
        fig_sub = apply_plotly_theme(fig_sub, height=320, title="Quantidade de Incidentes por Subcategoria")

    st.plotly_chart(fig_sub, use_container_width=True)

with col_g2:
    prio_counts = df_filtered["Nível de Prioridade"].value_counts().reset_index()
    prio_counts.columns = ["Prioridade", "Quantidade"]
    prio_counts = prio_counts.sort_values(by="Quantidade", ascending=True)

    fig_prio = px.bar(
        prio_counts,
        x="Quantidade",
        y="Prioridade",
        orientation="h",
        text="Quantidade",
        color_discrete_sequence=[colors["primary_light"]]
    )
    fig_prio.update_traces(textposition="outside", texttemplate="%{x:,.0f}")
    fig_prio = apply_plotly_theme(fig_prio, height=320, title="Distribuição por Nível de Prioridade")
    st.plotly_chart(fig_prio, use_container_width=True)

render_section_header("Comparativos Temporais Específicos", "Selecione períodos distintos para avaliar variações absolutas e percentuais.")

# 5. Fragmento para Comparativos Interativos
@st.fragment
def render_temporal_comparators():
    comp_tipo = st.segmented_control(
        "Escala temporal de comparação:",
        options=["Comparação Anual", "Comparação Mensal", "Comparação Diária"],
        default="Comparação Anual"
    )

    df_base = df_raw if df_raw is not None else df_filtered

    if comp_tipo == "Comparação Anual":
        anos = sorted(df_base["Ano_Abertura"].dropna().unique().tolist())
        if len(anos) >= 2:
            c1, c2 = st.columns(2)
            ano_a = c1.selectbox("Ano Base (A):", anos, index=0)
            ano_b = c2.selectbox("Ano Comparado (B):", anos, index=len(anos)-1)

            res = compare_annual(df_base, ano_a, ano_b)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"Chamados em {ano_a}", format_number_br(res["qtd_a"]))
            m2.metric(f"Chamados em {ano_b}", format_number_br(res["qtd_b"]))
            m3.metric("Diferença Absoluta", f"{res['diff_abs']:+d} chamados")
            m4.metric("Variação Percentual", format_percent_br(res["diff_pct"]))

            st.caption("Detalhamento por categoria entre os anos:")
            tabela_cat = res["tabela_categorias"].copy()
            tabela_cat["Var_Percentual"] = tabela_cat["Var_Percentual"].apply(format_percent_br)
            st.dataframe(tabela_cat, use_container_width=True, hide_index=True)
        else:
            st.info("Necessário pelo menos 2 anos distintos na base de dados.")

    elif comp_tipo == "Comparação Mensal":
        meses = sorted(df_base["Ano_Mes_Abertura"].dropna().unique().tolist())
        if len(meses) >= 2:
            c1, c2 = st.columns(2)
            mes_a = c1.selectbox("Mês Base (A):", meses, index=0)
            mes_b = c2.selectbox("Mês Comparado (B):", meses, index=len(meses)-1)

            res = compare_monthly(df_base, mes_a, mes_b)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"Chamados em {mes_a}", format_number_br(res["qtd_a"]))
            m2.metric(f"Chamados em {mes_b}", format_number_br(res["qtd_b"]))
            m3.metric("Diferença Absoluta", f"{res['diff_abs']:+d}")
            m4.metric("Variação Percentual", format_percent_br(res["diff_pct"]))
        else:
            st.info("Necessário pelo menos 2 meses distintos na base de dados.")

    elif comp_tipo == "Comparação Diária":
        dias = sorted(df_base["Data_Abertura_Dia"].dropna().unique().tolist())
        if len(dias) >= 2:
            c1, c2 = st.columns(2)
            dia_a = c1.selectbox("Dia Base (A):", dias, index=0)
            dia_b = c2.selectbox("Dia Comparado (B):", dias, index=len(dias)-1)

            res = compare_daily(df_base, dia_a, dia_b)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric(f"Chamados em {dia_a.strftime('%d/%m/%Y')}", format_number_br(res["qtd_a"]))
            m2.metric(f"Chamados em {dia_b.strftime('%d/%m/%Y')}", format_number_br(res["qtd_b"]))
            m3.metric("Diferença Absoluta", f"{res['diff_abs']:+d}")
            m4.metric("Variação Percentual", format_percent_br(res["diff_pct"]))

render_temporal_comparators()
