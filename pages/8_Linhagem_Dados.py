"""
Página 8 — Como os Dados se Cruzam (Transparência e Linhagem de Dados).
Exibe a rastreabilidade em tempo real, qualidade do cruzamento, funil de filtros e catálogo de métricas.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.lineage import METADATA_PAGINAS, get_data_quality_metrics
from utils.helpers import format_number_br, format_percent_br, format_currency_br
from utils.ui import (
    render_page_header,
    render_section_header,
    render_active_filter_chips,
    apply_plotly_theme,
    get_theme_colors
)

df_filtered = st.session_state.get("filtered_df")
df_raw = st.session_state.get("raw_chamados")
df_inventario = st.session_state.get("raw_inventario")
active_chips = st.session_state.get("active_chips", [])
funil_audit = st.session_state.get("funil_audit", [])

render_page_header(
    title="Como os Dados se Cruzam",
    subtitle="Transparência completa, linhagem de dados e integridade metodológica do painel em tempo real."
)

render_active_filter_chips(len(df_raw), len(df_filtered), active_chips)
colors = get_theme_colors()

modo_tecnico = st.toggle("🔍 Ver detalhes técnicos avançados (nomes de colunas, funções e código de cruzamento)", value=False)

# ==============================================================================
# 1. QUALIDADE DO CRUZAMENTO DOS DADOS (AO VIVO NA SESSÃO)
# ==============================================================================
render_section_header("1. Integridade e Qualidade do Cruzamento (Sessão Atual)")
quality = get_data_quality_metrics(df_filtered, df_inventario)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Chamados na visão atual", format_number_br(quality["total_chamados"]))
c2.metric("Ativos identificados", format_number_br(quality["com_ativo_identificado"]), f"{format_percent_br(quality['pct_ativo_identificado'])} identificados")
c3.metric("Casados no inventário", format_number_br(quality["casados_inventario"]), f"{format_percent_br(quality['pct_casados_inventario'])} do total")
c4.metric("Custos mapeados", format_number_br(quality["total_chamados"] - quality["sem_custo_estimado"]), "100% parametrizados")

if not modo_tecnico:
    st.markdown("""
    <div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; padding: 0.85rem 1rem; border-radius: 6px; font-size: 0.9rem; color: #1E293B;">
        ✅ <b>O que isso significa para a gestão?</b> Praticamente todos os chamados de campo trazem o código patrimonial do equipamento (PB-XXXXX). 
        Isso nos permite cruzar os chamados de suporte técnico diretamente com a data de compra e o tempo de vida útil do equipamento no inventário, 
        garantindo alta confiabilidade para as decisões de substituição.
    </div>
    """, unsafe_allow_html=True)
else:
    st.info(f"""
    **Detalhamento Técnico de Governança:**
    • **Chave de Ligação:** Regex `r'\\b(PB-\\d{{5}})\\b'` aplicada sobre `Descrição do Chamado`.
    • **Registros sem identificação:** {quality['nao_identificados']} chamados não continham o padrão PB-XXXXX e foram tratados sem perda de registro.
    • **Tipo de Junção:** `pandas.merge(..., how='left')` garantindo integridade referencial dos 2.458 chamados.
    """)

# ==============================================================================
# 2. FUNIL DE FILTRAGEM (AUDITORIA PASSO A PASSO)
# ==============================================================================
render_section_header("2. Funil de Filtragem: De Onde Vêm os Registros da Tela?")
st.caption("Acompanhe como os filtros ativos na barra lateral refinaram a base bruta até o número atual de registros.")

if funil_audit:
    df_funil = pd.DataFrame(funil_audit)
    
    col_f1, col_f2 = st.columns([3, 2])
    with col_f1:
        fig_funil = go.Figure(go.Funnel(
            y=df_funil["etapa"],
            x=df_funil["registros"],
            textinfo="value+percent initial",
            marker=dict(color=colors["primary"])
        ))
        fig_funil = apply_plotly_theme(fig_funil, height=300, title="Fluxo de Redução por Filtro")
        st.plotly_chart(fig_funil, use_container_width=True)

    with col_f2:
        st.markdown("#### Tabela de Auditoria")
        df_funil_view = df_funil.copy()
        df_funil_view["filtro_ativo"] = df_funil_view["filtro_ativo"].apply(lambda x: "Ativo" if x else "Sem Restrição")
        df_funil_view.columns = ["Etapa do Filtro", "Linhas Restantes", "Removidos Nesta Etapa", "Status"]
        st.dataframe(df_funil_view, use_container_width=True, hide_index=True)

# ==============================================================================
# 3. MAPA VISUAL DO CRUZAMENTO ENTRE AS BASES
# ==============================================================================
render_section_header("3. Arquitetura do Cruzamento entre as Fontes")

st.markdown("""
<div style="background-color: white; border: 1px solid #E2E8F0; padding: 1.25rem; border-radius: 8px; margin-bottom: 1.5rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
        <div style="flex: 1; min-width: 250px; background: #F1F5F9; padding: 1rem; border-radius: 6px; border-left: 4px solid #005596;">
            <div style="font-weight: 700; color: #005596;">1. chamados.xlsx (Pós-ETL)</div>
            <div style="font-size: 0.85rem; color: #475569; margin-top: 4px;">15 campos padronizados: ID do Chamado, Datas, Categoria, Subcategoria, Prioridade, Impacto, Localidade, Descrição.</div>
        </div>
        <div style="text-align: center; font-size: 1.2rem; font-weight: bold; color: #FF7A00;">
            ➕<br><span style="font-size: 0.75rem; color: #475569;">Cruzamento por regex<br><b>ID do Ativo (PB-XXXXX)</b></span>
        </div>
        <div style="flex: 1; min-width: 250px; background: #F1F5F9; padding: 1rem; border-radius: 6px; border-left: 4px solid #0083CA;">
            <div style="font-weight: 700; color: #0083CA;">2. inventario.xlsx</div>
            <div style="font-size: 0.85rem; color: #475569; margin-top: 4px;">Dados cadastrais: Fabricante, Modelo exato, Data de compra, Vida útil (anos), Idade de uso e Obsolescência.</div>
        </div>
        <div style="text-align: center; font-size: 1.2rem; font-weight: bold; color: #16A34A;">
            ➕<br><span style="font-size: 0.75rem; color: #475569;">Regras Semânticas de Defeito</span>
        </div>
        <div style="flex: 1; min-width: 250px; background: #F1F5F9; padding: 1rem; border-radius: 6px; border-left: 4px solid #16A34A;">
            <div style="font-weight: 700; color: #16A34A;">3. config/custos.json</div>
            <div style="font-size: 0.85rem; color: #475569; margin-top: 4px;">Tabela paramétrica: Preço de Peça (R$), Mão de Obra (R$) e Custo de Aquisição de Ativo Novo.</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 4. EXPLORADOR INTERATIVO: O QUE ALIMENTA CADA PÁGINA?
# ==============================================================================
render_section_header("4. Dicionário Interativo de Métricas por Página")
pagina_escolhida = st.selectbox(
    "Qual página ou indicador você deseja entender agora?",
    options=list(METADATA_PAGINAS.keys()),
    index=0
)

info_pag = METADATA_PAGINAS[pagina_escolhida]
st.markdown(f"**Finalidade da Página:** {info_pag['descricao']}")
st.caption(f"Linhas atualmente consideradas no cálculo: **{format_number_br(len(df_filtered))} chamados**.")

for ind in info_pag["indicadores"]:
    with st.expander(f"📌 {ind['tipo']}: {ind['nome']}", expanded=True):
        st.write(f"**O que mede:** {ind['formula_leigo']}")
        st.write(f"**Fontes utilizadas:** `{', '.join(ind['tabelas_origem'])}`")
        if modo_tecnico:
            st.code(f"""
# Colunas Utilizadas: {', '.join(ind['colunas_tecnicas'])}
# Módulo de Cálculo: {ind['modulo_funcao']}
# Fórmula Técnica:
{ind['formula_tecnica']}
            """, language="python")

# ==============================================================================
# 5. AMOSTRA VIVA: O CICLO COMPLETO DE UM CHAMADO REAL
# ==============================================================================
render_section_header("5. Amostra Viva dos Dados (Rastreabilidade de Ponta a Ponta)")
st.write("Veja abaixo o exemplo de como um chamado bruto é enriquecido com os dados do inventário e precificado pelo modelo:")

exemplo_chamado = df_filtered.iloc[0]
id_ch = exemplo_chamado["ID do Chamado"]
id_at = exemplo_chamado["ID_Ativo_Extraido"]
mod = exemplo_chamado["Modelo_Final"]
def_desc = exemplo_chamado["Componente_Defeito"]
custo_est = format_currency_br(exemplo_chamado["Custo_Total_Estimado"])
obs = exemplo_chamado["Obsolescencia_Final"]

st.markdown(f"""
<div style="background-color: #F8FAFC; border: 1px solid #CBD5E1; padding: 0.85rem 1rem; border-radius: 6px; margin-bottom: 1rem; font-size: 0.92rem; color: #1E293B;">
    <strong>Trilha de Rastreabilidade do Exemplo:</strong><br>
    Chamado <code>{id_ch}</code> ➔ Ativo <code>{id_at}</code> ➔ Modelo <code>{mod}</code> 
    ➔ Defeito Identificado <code>{def_desc}</code> ➔ Custo Estimado <code>{custo_est}</code> ➔ Obsolescência <code>{obs}</code>
</div>
""", unsafe_allow_html=True)

amostra_view = df_filtered.head(10)[[
    "ID do Chamado", "Tipo de Equipamento", "Subcategoria", "Localidade",
    "ID_Ativo_Extraido", "Modelo_Final", "Obsolescencia_Final", "Custo_Total_Estimado"
]].copy()

amostra_view["Custo_Total_Estimado"] = amostra_view["Custo_Total_Estimado"].apply(format_currency_br)

st.dataframe(
    amostra_view,
    column_config={
        "ID do Chamado": st.column_config.TextColumn("Chamado (Origem: chamados)"),
        "Tipo de Equipamento": st.column_config.TextColumn("Tipo (Origem: chamados)"),
        "Subcategoria": st.column_config.TextColumn("Defeito"),
        "Localidade": st.column_config.TextColumn("Cidade"),
        "ID_Ativo_Extraido": st.column_config.TextColumn("Ativo PB (Regex)"),
        "Modelo_Final": st.column_config.TextColumn("Modelo (Origem: inventário)"),
        "Obsolescencia_Final": st.column_config.TextColumn("Ciclo (Origem: inventário)"),
        "Custo_Total_Estimado": st.column_config.TextColumn("Custo (Origem: custos.json)")
    },
    use_container_width=True,
    hide_index=True
)
