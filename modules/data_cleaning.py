"""
Módulo de tratamento, limpeza e enriquecimento de dados.
Executa padronização de datas, extração de identificadores de ativos por regex,
cálculo de tempos de resolução e estouro de SLA, e junção com o inventário.
"""
import re
import pandas as pd
import streamlit as st
from modules.data_loader import load_chamados_raw, load_inventario_raw

@st.cache_data(show_spinner="Higienizando e cruzando dados...")
def get_clean_data():
    """
    Retorna dois DataFrames tratados e enriquecidos:
    1. df_chamados: Chamados de incidentes com métricas de tempo, SLA, ID do ativo e dados do inventário.
    2. df_inventario: Base de inventário higienizada com categorização do ciclo de vida.
    """
    df_chamados = load_chamados_raw().copy()
    df_inventario = load_inventario_raw().copy()

    # 1. Padronização de colunas de texto no inventário
    for col in df_inventario.columns:
        if df_inventario[col].dtype == "object":
            df_inventario[col] = df_inventario[col].astype(str).str.strip()

    if "Data de compra" in df_inventario.columns:
        df_inventario["Data de compra"] = pd.to_datetime(df_inventario["Data de compra"], errors="coerce")

    # Classificação do ciclo de vida no inventário
    def classificar_ciclo_vida(row):
        try:
            idade = float(row.get("Idade de uso (anos)", 0))
            vida_util = float(row.get("Vida útil (anos)", 3))
            obs = str(row.get("Obsolescência", "")).lower()
            if "obsoleto" in obs or idade >= vida_util:
                return "Obsoleto / Vencido"
            elif idade >= (vida_util - 0.5):
                return "Próximo à Obsolescência"
            else:
                return "Dentro da Vida Útil"
        except Exception:
            return "Indefinido"

    df_inventario["Ciclo_Vida"] = df_inventario.apply(classificar_ciclo_vida, axis=1)

    # 2. Tratamento da base de chamados
    for col in df_chamados.columns:
        if df_chamados[col].dtype == "object":
            df_chamados[col] = df_chamados[col].astype(str).str.strip()

    # Conversão de datas
    date_cols = ["Data de Abertura", "Data de Solução Prevista", "Data de Resolução"]
    for col in date_cols:
        if col in df_chamados.columns:
            df_chamados[col] = pd.to_datetime(df_chamados[col], errors="coerce")

    # Extração de componentes de tempo
    df_chamados["Ano_Abertura"] = df_chamados["Data de Abertura"].dt.year
    df_chamados["Mes_Abertura"] = df_chamados["Data de Abertura"].dt.month
    df_chamados["Ano_Mes_Abertura"] = df_chamados["Data de Abertura"].dt.strftime("%Y-%m")
    df_chamados["Data_Abertura_Dia"] = df_chamados["Data de Abertura"].dt.date

    # Cálculo do tempo de resolução (MTTR) em horas e dias
    df_chamados["Tempo_Resolucao_Horas"] = (
        (df_chamados["Data de Resolução"] - df_chamados["Data de Abertura"]).dt.total_seconds() / 3600.0
    ).clip(lower=0)
    df_chamados["Tempo_Resolucao_Dias"] = df_chamados["Tempo_Resolucao_Horas"] / 24.0

    # Cumprimento de SLA (considera estouro se resolvido após a data prevista)
    df_chamados["SLA_Estourado"] = df_chamados["Data de Resolução"] > df_chamados["Data de Solução Prevista"]
    df_chamados["SLA_Status"] = df_chamados["SLA_Estourado"].apply(lambda x: "Estourado" if x else "No Prazo")

    # Extração do ID do Ativo físico (PB-XXXXX) do texto da Descrição
    def extrair_id_ativo(desc):
        if not isinstance(desc, str):
            return "Não Identificado"
        match = re.search(r"\b(PB-\d{5})\b", desc)
        return match.group(1) if match else "Não Identificado"

    df_chamados["ID_Ativo_Extraido"] = df_chamados["Descrição do Chamado"].apply(extrair_id_ativo)

    # Extração do Modelo do Equipamento a partir do Resumo / Descrição
    def extrair_modelo(row):
        resumo = str(row.get("Resumo do Chamado", ""))
        if "—" in resumo:
            partes = resumo.split("—")
            return partes[-1].strip()
        desc = str(row.get("Descrição do Chamado", ""))
        match = re.search(r"PB-\d{5}\s*\((.*?)\)", desc)
        if match:
            return match.group(1).strip()
        return row.get("Tipo de Equipamento", "Não Identificado")

    df_chamados["Modelo_Identificado"] = df_chamados.apply(extrair_modelo, axis=1)

    # Cruzamento com o inventário
    df_inv_merge = df_inventario[[
        "ID do ativo", "Fabricante", "Modelo", "Vida útil (anos)",
        "Idade de uso (anos)", "Obsolescência", "Ciclo_Vida", "Status"
    ]].rename(columns={"Status": "Status_Ativo_Inventario"})

    df_chamados = df_chamados.merge(
        df_inv_merge,
        left_on="ID_Ativo_Extraido",
        right_on="ID do ativo",
        how="left"
    )

    # Se o modelo do inventário existir, usar preferencialmente
    df_chamados["Modelo_Final"] = df_chamados["Modelo"].combine_first(df_chamados["Modelo_Identificado"])
    df_chamados["Obsolescencia_Final"] = df_chamados["Obsolescência"].fillna("Não Mapeado")

    return df_chamados, df_inventario
