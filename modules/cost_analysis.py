"""
Módulo de análise e cálculo de custos de manutenção.
Cruza as ocorrências com a tabela paramétrica custos.json (peças, mão de obra e serviços).
Diferencia custos registrados (inexistentes na base original) de custos estimados pelo modelo.
"""
from typing import Dict, Any, Tuple
import pandas as pd
import streamlit as st
from modules.data_loader import load_custos_config

def estimar_custo_chamado(row: pd.Series, config_custos: Dict[str, Any]) -> Tuple[str, str, float, float, float]:
    """
    Regra de associação semântica entre os sintomas do chamado e a tabela paramétrica.
    Retorna: (Tipo_Custo, Componente_Servico, Custo_Peca, Custo_Mao_Obra, Custo_Total)
    """
    tipo_eq = str(row.get("Tipo de Equipamento", "")).strip()
    subcat = str(row.get("Subcategoria", "")).lower()
    desc = str(row.get("Descrição do Chamado", "")).lower()
    resumo = str(row.get("Resumo do Chamado", "")).lower()
    texto_busca = f"{subcat} {resumo} {desc}"

    regras = config_custos.get("regras_de_custo", {}).get(tipo_eq, {})

    # 1. Busca por regras de componentes do tipo de equipamento
    for comp_key, comp_val in regras.items():
        termos = comp_val.get("termos", [])
        if any(termo in texto_busca for termo in termos):
            peca = float(comp_val.get("peca", 0.0))
            mo = float(comp_val.get("mao_de_obra", 0.0))
            total = float(comp_val.get("total", peca + mo))
            tipo_class = "Serviço Lógico" if peca == 0 else "Substituição de Peça"
            return tipo_class, comp_key.replace("_", " ").title(), peca, mo, total

    # 2. Se for problema puramente lógico/sistema
    if any(p in texto_busca for p in ["lentidão", "travamento", "aplicativo", "erro", "reinicialização"]):
        mo = float(config_custos.get("servicos_tecnicos_gerais", {}).get("recuperacao_configuracao_software", 90.0))
        return "Serviço Lógico", "Recuperação Lógica / Software", 0.0, mo, mo

    # 3. Caso não mapeado: diagnóstico básico padrão
    mo_diag = float(config_custos.get("servicos_tecnicos_gerais", {}).get("diagnostico_tecnico", 45.0))
    return "Diagnóstico Técnico", "Inspeção e Testes Técnicos", 0.0, mo_diag, mo_diag

@st.cache_data
def aplicar_custos(df_chamados: pd.DataFrame) -> pd.DataFrame:
    """Aplica o cálculo de custos em todo o dataframe de chamados."""
    df = df_chamados.copy()
    config = load_custos_config()

    resultados = df.apply(lambda row: estimar_custo_chamado(row, config), axis=1)

    df["Tipo_Custo"] = [r[0] for r in resultados]
    df["Componente_Defeito"] = [r[1] for r in resultados]
    df["Custo_Peca"] = [r[2] for r in resultados]
    df["Custo_Mao_Obra"] = [r[3] for r in resultados]
    df["Custo_Total_Estimado"] = [r[4] for r in resultados]

    return df

def get_cost_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """Retorna KPIs consolidados de custo."""
    total_custo = df["Custo_Total_Estimado"].sum()
    total_pecas = df["Custo_Peca"].sum()
    total_mo = df["Custo_Mao_Obra"].sum()
    total_chamados = len(df)
    custo_medio = total_custo / total_chamados if total_chamados > 0 else 0.0

    return {
        "custo_total": total_custo,
        "custo_pecas": total_pecas,
        "custo_mao_obra": total_mo,
        "custo_medio_incidente": custo_medio,
        "pct_pecas": (total_pecas / total_custo * 100) if total_custo > 0 else 0.0,
        "pct_mao_obra": (total_mo / total_custo * 100) if total_custo > 0 else 0.0
    }

def get_costs_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Agrupamento de custos por Tipo de Equipamento."""
    return df.groupby("Tipo de Equipamento").agg(
        Total_Incidentes=("ID do Chamado", "count"),
        Custo_Total=("Custo_Total_Estimado", "sum"),
        Custo_Pecas=("Custo_Peca", "sum"),
        Custo_Mao_Obra=("Custo_Mao_Obra", "sum"),
        Custo_Medio=("Custo_Total_Estimado", "mean")
    ).reset_index().sort_values(by="Custo_Total", ascending=False)

def get_costs_by_model(df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """Agrupamento de custos por Modelo de Equipamento."""
    return df.groupby(["Tipo de Equipamento", "Modelo_Final"]).agg(
        Total_Incidentes=("ID do Chamado", "count"),
        Custo_Total=("Custo_Total_Estimado", "sum"),
        Custo_Medio=("Custo_Total_Estimado", "mean")
    ).reset_index().sort_values(by="Custo_Total", ascending=False).head(top_n)

def get_cost_temporal(df: pd.DataFrame) -> pd.DataFrame:
    """Evolução mensal dos custos de manutenção."""
    df_temp = df.dropna(subset=["Data de Abertura"]).copy()
    return df_temp.groupby("Ano_Mes_Abertura").agg(
        Custo_Total=("Custo_Total_Estimado", "sum"),
        Custo_Pecas=("Custo_Peca", "sum"),
        Custo_Mao_Obra=("Custo_Mao_Obra", "sum"),
        Incidentes=("ID do Chamado", "count")
    ).reset_index().sort_values(by="Ano_Mes_Abertura")
