"""
Página 6 — Substituição vs. Manutenção.
Responde à pergunta estratégica: Quando é mais vantajoso substituir um equipamento?
Análise de trade-off financeiro, ponto de equilíbrio e simulador de cenários.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from modules.replacement_analysis import get_asset_replacement_analysis, simulate_projection_scenarios
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
df_inventario = st.session_state.get("raw_inventario")
active_chips = st.session_state.get("active_chips", [])

if df_filtered is None or df_inventario is None:
    render_page_header("Substituição vs. Manutenção", "Análise de Trade-off e Ponto de Equilíbrio.")
    render_empty_state()
    st.stop()

colors = get_theme_colors()

# 1. Dialog para Inspecionar Ativo
@st.dialog("Ficha de Decisão de Substituição do Ativo")
def show_replacement_dialog(row_dict: dict):
    st.markdown(f"### Ativo: **{row_dict['ID do ativo']}** — {row_dict['Modelo']}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Custo total de reparos", format_currency_br(row_dict["Custo_Acumulado_Manutencao"]))
    c2.metric("Preço de um novo", format_currency_br(row_dict["Preco_Estimado_Novo"]))
    c3.metric("% Comprometido", f"{row_dict['Pct_Gasto_Em_Manutencao']:.1f}%".replace(".", ","))

    st.write(f"**Parecer:** {row_dict['Recomendacao_Gerencial']}")
    st.write(f"**Ciclo de vida:** {row_dict['Ciclo_Vida']} ({row_dict['Idade de uso (anos)']} anos de uso)")
    st.write(f"**Falhas recorrentes:** {row_dict['Principais_Defeitos']}")
    st.write(f"**Localidade:** {row_dict['Cidade de operação']}")

# 2. Fragmento Interativo de Trade-off
@st.fragment
def render_tradeoff_simulator():
    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        limite_corte = st.slider(
            "Ponto de Corte de Manutenção (% do Valor de um Ativo Novo):",
            min_value=25,
            max_value=75,
            value=50,
            step=5,
            help="Critério de trade-off: se a soma de reparos ultrapassar esse limite, o BI recomenda a substituição."
        )
    with col_ctrl2:
        st.markdown(f"""
        <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.75rem; border-radius: 6px; font-size: 0.85rem; margin-top: 0.5rem; color: #334155;">
            <b>Regra Ativa:</b> Substituir se Custo Reparos $\ge$ <b>{limite_corte}%</b> do novo ou se obsoleto e reincidente.
        </div>
        """, unsafe_allow_html=True)

    df_rep = get_asset_replacement_analysis(df_filtered, df_inventario, limite_pct=limite_corte / 100.0)

    # Contagens
    tot = len(df_rep)
    qtd_subst = (df_rep["Recomendacao_Gerencial"] == "Substituir Imediatamente").sum()
    qtd_monit = (df_rep["Recomendacao_Gerencial"] == "Monitorar / Planejar Troca").sum()
    qtd_ok = (df_rep["Recomendacao_Gerencial"] == "Manter em Operação").sum()

    pct_subst_str = f"{(qtd_subst/tot)*100:.1f}%".replace(".", ",")

    # Cards de KPIs (Sem reticências)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ativos monitorados", format_number_br(tot))
    c2.metric("Substituir imediatamente", format_number_br(qtd_subst), f"{pct_subst_str} do parque", delta_color="inverse")
    c3.metric("Planejar substituição", format_number_br(qtd_monit))
    c4.metric("Manter em operação", format_number_br(qtd_ok))

    render_section_header("Relação entre Idade do Equipamento e Custo Acumulado de Reparo")

    fig_disp = px.scatter(
        df_rep,
        x="Idade de uso (anos)",
        y="Custo_Acumulado_Manutencao",
        color="Recomendacao_Gerencial",
        size="Total_Chamados",
        hover_data=["ID do ativo", "Modelo", "Pct_Gasto_Em_Manutencao"],
        color_discrete_map={
            "Substituir Imediatamente": colors["danger"],
            "Monitorar / Planejar Troca": colors["warning"],
            "Manter em Operação": colors["success"]
        }
    )
    fig_disp = apply_plotly_theme(fig_disp, height=330, title="Idade vs. Custo Acumulado (Tamanho da bolha = Qtd Chamados)", show_legend=True)
    st.plotly_chart(fig_disp, use_container_width=True)

    render_section_header("Simulação Financeira de Cenários (Projeção Futura)")

    c_cat, c_horiz = st.columns([2, 1])
    with c_cat:
        cat_sim = st.selectbox("Categoria para a Projeção:", df_rep["Tipo de equipamento"].unique(), index=0)
    with c_horiz:
        horizonte = st.segmented_control("Horizonte:", options=[12, 24, 36], default=24)

    sim_res = simulate_projection_scenarios(df_rep, cat_sim, horizonte_meses=horizonte)

    if sim_res:
        ponto_eq = sim_res.get("ponto_equilibrio_mes")
        ci1, ci2 = st.columns(2)
        ci1.metric("Investimento em novos (CAPEX)", format_currency_compact(sim_res["capex_aquisicao_novo"]), help=format_currency_br(sim_res["capex_aquisicao_novo"]))
        if ponto_eq:
            ci2.metric("Ponto de equilíbrio (Break-even)", f"{ponto_eq}º Mês", "Economia consolidada após esta data")
        else:
            ci2.info("Break-even estimado além do horizonte selecionado.")

        df_proj = sim_res["projeção_tabela"]
        fig_proj = go.Figure()
        fig_proj.add_trace(go.Scatter(
            x=df_proj["Mes"],
            y=df_proj["Continuar_Mantendo"],
            mode="lines+markers",
            name="Cenário A: Continuar Mantendo",
            line=dict(color=colors["danger"], width=2.5)
        ))
        fig_proj.add_trace(go.Scatter(
            x=df_proj["Mes"],
            y=df_proj["Substituir_Criticos"],
            mode="lines+markers",
            name="Cenário B: Substituição Planejada",
            line=dict(color=colors["primary"], width=2.5, dash="dash")
        ))
        fig_proj = apply_plotly_theme(fig_proj, height=300, title=f"Projeção de Custos Acumulados — {cat_sim} ({horizonte} Meses)", show_legend=True)
        st.plotly_chart(fig_proj, use_container_width=True)

    render_section_header("Equipamentos Críticos Elegíveis para Substituição Imediata")

    df_top_sub = df_rep[df_rep["Recomendacao_Gerencial"] == "Substituir Imediatamente"].copy()
    
    # 6 colunas essenciais
    df_table_sub = df_top_sub[[
        "ID do ativo", "Modelo", "Cidade de operação",
        "Total_Chamados", "Pct_Gasto_Em_Manutencao", "Custo_Acumulado_Manutencao"
    ]].copy()

    df_table_sub["Custo_Acumulado_Manutencao"] = df_table_sub["Custo_Acumulado_Manutencao"].apply(format_currency_br)

    st.dataframe(
        df_table_sub.head(10),
        column_config={
            "ID do ativo": st.column_config.TextColumn("Código Ativo"),
            "Total_Chamados": st.column_config.NumberColumn("Chamados"),
            "Pct_Gasto_Em_Manutencao": st.column_config.ProgressColumn(
                "% Gasto / Novo",
                format="%.1f%%",
                min_value=0,
                max_value=150
            ),
            "Custo_Acumulado_Manutencao": st.column_config.TextColumn("Custo Acumulado")
        },
        use_container_width=True,
        hide_index=True
    )

    with st.expander("Consultar detalhes de um ativo específico"):
        ativo_escolhido = st.selectbox("Selecione o ativo:", df_top_sub["ID do ativo"].unique())
        if ativo_escolhido:
            dados_ativo = df_top_sub[df_top_sub["ID do ativo"] == ativo_escolhido].iloc[0].to_dict()
            if st.button("Abrir ficha completa"):
                show_replacement_dialog(dados_ativo)

# Header e Insight da Página
df_pre_rep = get_asset_replacement_analysis(df_filtered, df_inventario, limite_pct=0.50)
qtd_pre_sub = (df_pre_rep["Recomendacao_Gerencial"] == "Substituir Imediatamente").sum()

insight_texto = (
    f"Existem <b>{format_number_br(qtd_pre_sub)} equipamentos</b> cujo custo acumulado de reparos já "
    f"ultrapassou <b>50% do valor de um aparelho novo</b>, sendo candidatos prioritários para descarte e renovação."
)

render_page_header(
    title="Substituição vs. Manutenção",
    subtitle="Modelagem de Trade-off e Ponto de Equilíbrio para apoiar decisões de CAPEX vs. OPEX.",
    insight=insight_texto
)

# Barra de Filtros Ativos
render_active_filter_chips(len(df_raw), len(df_filtered), active_chips)

# Execução do simulador
render_tradeoff_simulator()
