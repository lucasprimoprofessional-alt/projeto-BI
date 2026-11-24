"""
Aplicação Principal de Business Intelligence (BI) — Energisa Paraíba.
Arquitetura moderna com st.navigation, CSS corporativo e governança de dados.
"""
import streamlit as st
import pandas as pd
from modules.data_cleaning import get_clean_data
from modules.cost_analysis import aplicar_custos
from utils.ui import inject_custom_css
from utils.filters import render_sidebar_controls, apply_filters

# 1. Configuração da Página
st.set_page_config(
    page_title="BI Gestão de Ativos | Energisa Paraíba",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Injeção de CSS Minimalista
inject_custom_css()

# 3. Carregamento e Enriquecimento Unificado de Dados
df_chamados_raw, df_inventario = get_clean_data()
df_chamados = aplicar_custos(df_chamados_raw)

# Armazenamento das bases puras em session_state
st.session_state["raw_chamados"] = df_chamados
st.session_state["raw_inventario"] = df_inventario

# 4. Renderização dos Filtros na Sidebar e Aplicação Centralizada
render_sidebar_controls(df_chamados)
df_filtered, active_chips, funil_audit = apply_filters(df_chamados)

# Persistência do estado filtrado e de auditoria para todas as páginas
st.session_state["filtered_df"] = df_filtered
st.session_state["active_chips"] = active_chips
st.session_state["funil_audit"] = funil_audit

# 5. Definição da Navegação Estruturada por Seções com st.navigation
pages = {
    "Visão Geral": [
        st.Page("pages/1_Visao_Executiva.py", title="Visão Executiva", icon=":material/dashboard:", default=True)
    ],
    "Operação & Ativos": [
        st.Page("pages/2_Incidentes.py", title="Incidentes", icon=":material/report_problem:"),
        st.Page("pages/3_Equipamentos.py", title="Equipamentos & Obsolescência", icon=":material/devices:"),
        st.Page("pages/4_Ranking.py", title="Ranking de Reincidência", icon=":material/format_list_numbered:"),
        st.Page("pages/7_Impacto_Operacional.py", title="Impacto Operacional", icon=":material/bolt:")
    ],
    "Estratégia & Custos": [
        st.Page("pages/5_Custos.py", title="Custos de Manutenção", icon=":material/payments:"),
        st.Page("pages/6_Substituicao.py", title="Substituição vs. Manutenção", icon=":material/published_with_changes:")
    ],
    "Transparência & Linhagem": [
        st.Page("pages/8_Linhagem_Dados.py", title="Como os Dados se Cruzam", icon=":material/schema:")
    ]
}

pg = st.navigation(pages)
pg.run()
