"""
Módulo de análise de impacto na operação de campo e disponibilidade.
Analisa severidade, cumprimento de SLA, tempo médio de resolução (MTTR) e distribuição geográfica por município.
Documenta a diferença metodológica entre Tempo de Atendimento e Indisponibilidade Real.
"""
from typing import Dict, Any
import pandas as pd

def get_operational_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Retorna KPIs operacionais de campo."""
    total = len(df)
    if total == 0:
        return {
            "mttr_medio_horas": 0.0,
            "mttr_medio_dias": 0.0,
            "taxa_sla_cumprido": 0.0,
            "chamados_alto_impacto": 0,
            "chamados_criticos": 0,
            "total_localidades_atendidas": 0
        }

    mttr_h = df["Tempo_Resolucao_Horas"].dropna().mean()
    mttr_d = df["Tempo_Resolucao_Dias"].dropna().mean()
    sla_ok = (~df["SLA_Estourado"]).sum()
    taxa_sla = (sla_ok / total) * 100.0

    alto_impacto = (df["Impacto Causado"] == "Alto").sum()
    criticos = (df["Nível de Prioridade"] == "Crítico").sum()
    localidades = df["Localidade"].nunique()

    return {
        "mttr_medio_horas": float(mttr_h) if not pd.isna(mttr_h) else 0.0,
        "mttr_medio_dias": float(mttr_d) if not pd.isna(mttr_d) else 0.0,
        "taxa_sla_cumprido": taxa_sla,
        "chamados_alto_impacto": int(alto_impacto),
        "chamados_criticos": int(criticos),
        "total_localidades_atendidas": localidades
    }

def get_impact_by_location(df: pd.DataFrame) -> pd.DataFrame:
    """Análise de impacto e volume por localidade (cidades da Paraíba)."""
    return df.groupby("Localidade").agg(
        Total_Chamados=("ID do Chamado", "count"),
        Alto_Impacto=("Impacto Causado", lambda x: (x == "Alto").sum()),
        SLA_Estourado=("SLA_Estourado", "sum"),
        MTTR_Medio_Horas=("Tempo_Resolucao_Horas", "mean"),
        Custo_Total_Estimado=("Custo_Total_Estimado", "sum")
    ).reset_index().sort_values(by="Total_Chamados", ascending=False)

def get_impact_cross_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Matriz cruzada entre Nível de Prioridade e Impacto Causado."""
    return pd.crosstab(
        df["Nível de Prioridade"],
        df["Impacto Causado"],
        margins=True,
        margins_name="Total"
    )

def get_downtime_by_category(df: pd.DataFrame) -> pd.DataFrame:
    """Tempo médio e total de resolução por Tipo de Equipamento."""
    return df.groupby("Tipo de Equipamento").agg(
        Total_Chamados=("ID do Chamado", "count"),
        MTTR_Medio_Horas=("Tempo_Resolucao_Horas", "mean"),
        MTTR_Medio_Dias=("Tempo_Resolucao_Dias", "mean"),
        Horas_Totais_Atendimento=("Tempo_Resolucao_Horas", "sum"),
        Taxa_Quebra_SLA=("SLA_Estourado", lambda x: (x.sum() / len(x)) * 100 if len(x) > 0 else 0.0)
    ).reset_index().sort_values(by="MTTR_Medio_Horas", ascending=False)
