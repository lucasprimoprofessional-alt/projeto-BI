"""
Página 4 — Ranking de Reincidência.
Identificação dos ativos físicos mais problemáticos com drill-down detalhado em diálogo modal.
"""
import streamlit as st
import pandas as pd
from modules.equipment_analysis import get_top_recurring_equipment_by_category
from utils.helpers import format_number_br, format_currency_br, format_date_br
from utils.ui import (
    render_page_header,
    render_section_header,
    render_active_filter_chips,
    render_empty_state,
    get_theme_colors
)

df_filtered = st.session_state.get("filtered_df")
df_raw = st.session_state.get("raw_chamados")
active_chips = st.session_state.get("active_chips", [])

if df_filtered is None or df_filtered.empty:
    render_page_header("Ranking de Reincidência", "Identificação dos ativos mais ofensores.")
    render_empty_state()
    st.stop()

# 1. Dialog para Drill-Down do Ativo Físico
@st.dialog("Ficha de Auditoria e Histórico do Ativo")
def show_asset_audit_dialog(asset_id: str, df_history: pd.DataFrame):
    st.markdown(f"### Ativo: **{asset_id}**")
    
    total_calls = len(df_history)
    custo_total = df_history["Custo_Total_Estimado"].sum()
    modelo = df_history["Modelo_Final"].iloc[0] if not df_history.empty else "N/D"
    cidades = ", ".join(df_history["Localidade"].unique())

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de chamados", format_number_br(total_calls))
    c2.metric("Custo acumulado", format_currency_br(custo_total))
    c3.metric("Modelo", modelo)

    st.write(f"**Cidades de atuação:** {cidades}")
    st.markdown("#### Histórico Cronológico de Intervenções")

    df_view = df_history[[
        "ID do Chamado", "Data de Abertura", "Subcategoria",
        "Componente_Defeito", "Custo_Total_Estimado", "Nível de Prioridade", "Impacto Causado", "SLA_Status"
    ]].copy()
    df_view["Data de Abertura"] = df_view["Data de Abertura"].apply(format_date_br)
    df_view["Custo_Total_Estimado"] = df_view["Custo_Total_Estimado"].apply(format_currency_br)

    st.dataframe(df_view, use_container_width=True, hide_index=True)

# 2. Seletor de Categoria
categorias_disp = sorted(df_filtered["Tipo de Equipamento"].dropna().unique().tolist())

col_sel1, col_sel2 = st.columns([2, 3])
with col_sel1:
    categoria_alvo = st.selectbox("Selecione a Categoria de Equipamento:", categorias_disp, index=0)

# Top 3 da categoria
top3_df = get_top_recurring_equipment_by_category(df_filtered, categoria_alvo, top_n=3)

# Insight
if not top3_df.empty:
    top1_id = top3_df.iloc[0].get("ID_Ativo", top3_df.iloc[0].get("Equipamento_Modelo"))
    top1_qtd = top3_df.iloc[0]["Total_Chamados"]
    insight_texto = (
        f"O equipamento com maior reincidência na categoria <b>{categoria_alvo}</b> é o ativo <b>{top1_id}</b>, "
        f"com <b>{top1_qtd}</b> intervenções técnicas registradas."
    )
else:
    insight_texto = "Nenhum ativo individual reincidente identificado para a seleção atual."

render_page_header(
    title="Ranking de Reincidência",
    subtitle=f"Rastreabilidade cirúrgica dos ativos físicos (PB-XXXXX) com maior histórico de falhas.",
    insight=insight_texto
)

# Barra de Filtros Ativos
render_active_filter_chips(len(df_raw), len(df_filtered), active_chips)

render_section_header(f"Top 3 Equipamentos Mais Ofensores — {categoria_alvo}")

if top3_df.empty:
    st.info(f"Nenhum ativo com identificador individual encontrado para a categoria {categoria_alvo}.")
else:
    cols = st.columns(len(top3_df))
    for i, (_, row) in enumerate(top3_df.iterrows()):
        asset_id = str(row.get("ID_Ativo", row.get("Equipamento_Modelo")))
        with cols[i]:
            st.markdown(f"#### #{i+1} — {asset_id}")
            st.caption(f"Modelo: {row.get('Modelo', row.get('Equipamento_Modelo'))}")
            st.metric("Total de chamados", format_number_br(row["Total_Chamados"]))
            st.write(f"**Impacto predominante:** {row['Impacto_Predominante']}")
            if "Principais_Problemas" in row:
                st.write(f"**Falhas mais comuns:** {row['Principais_Problemas']}")
            
            if st.button(f"Ver Histórico ({asset_id})", key=f"btn_asset_{asset_id}_{i}", use_container_width=True):
                df_asset_history = df_filtered[
                    (df_filtered["ID_Ativo_Extraido"] == asset_id) |
                    (df_filtered["Modelo_Final"] == asset_id)
                ].sort_values(by="Data de Abertura", ascending=False)
                show_asset_audit_dialog(asset_id, df_asset_history)

render_section_header("Consulta Ampla de Ativos e Reincidência")

# Tabela consolidada de reincidentes
df_reincidentes = df_filtered[df_filtered["Tipo de Equipamento"] == categoria_alvo]
df_table_agg = df_reincidentes[df_reincidentes["ID_Ativo_Extraido"] != "Não Identificado"].groupby(
    ["ID_Ativo_Extraido", "Modelo_Final"]
).agg(
    Chamados=("ID do Chamado", "count"),
    Custo_Acumulado=("Custo_Total_Estimado", "sum"),
    Localidade_Principal=("Localidade", lambda x: x.mode()[0] if not x.empty else "-"),
    Principal_Falha=("Subcategoria", lambda x: x.mode()[0] if not x.empty else "-")
).reset_index().rename(columns={"ID_Ativo_Extraido": "ID do Ativo", "Modelo_Final": "Modelo"}).sort_values(by="Chamados", ascending=False)

df_table_agg["Custo_Acumulado"] = df_table_agg["Custo_Acumulado"].apply(format_currency_br)

st.dataframe(
    df_table_agg.head(15),
    column_config={
        "Chamados": st.column_config.NumberColumn("Qtd Chamados"),
        "Custo_Acumulado": st.column_config.TextColumn("Custo Total"),
    },
    use_container_width=True,
    hide_index=True
)
