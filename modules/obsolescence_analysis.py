"""
Módulo de gestão de equipamentos e obsolescência.
Classifica ativos pelo ciclo de vida e calcula o Score Composto de Atenção (Top Categorias).
"""
import pandas as pd

def get_obsolescence_distribution(df_inventario: pd.DataFrame) -> pd.DataFrame:
    """Distribuição geral e por categoria da situação de obsolescência."""
    return df_inventario.groupby(["Tipo de equipamento", "Ciclo_Vida"]).agg(
        Quantidade=("ID do ativo", "count")
    ).reset_index().rename(columns={"Tipo de equipamento": "Categoria"})

def get_obsolescence_summary_kpis(df_inventario: pd.DataFrame) -> dict:
    """Retorna métricas consolidadas de obsolescência do inventário."""
    total = len(df_inventario)
    if total == 0:
        return {"total": 0, "obsoletos": 0, "proximos": 0, "dentro_prazo": 0, "pct_obsoletos": 0.0}

    obsoletos = (df_inventario["Ciclo_Vida"] == "Obsoleto / Vencido").sum()
    proximos = (df_inventario["Ciclo_Vida"] == "Próximo à Obsolescência").sum()
    dentro = (df_inventario["Ciclo_Vida"] == "Dentro da Vida Útil").sum()

    return {
        "total": total,
        "obsoletos": int(obsoletos),
        "proximos": int(proximos),
        "dentro_prazo": int(dentro),
        "pct_obsoletos": (obsoletos / total) * 100.0,
        "pct_proximos": (proximos / total) * 100.0,
        "pct_dentro_prazo": (dentro / total) * 100.0
    }

def calculate_top_attention_categories(df_chamados: pd.DataFrame, df_inventario: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o Score Composto de Atenção para categorizar o nível de criticidade gerencial.
    Pesos documentados do modelo analítico:
    - Volume de incidentes: 30% (Peso 0.30)
    - Proporção de incidentes com impacto Alto: 25% (Peso 0.25)
    - Custo total estimado de manutenção: 25% (Peso 0.25)
    - Taxa de obsolescência de ativos na categoria: 20% (Peso 0.20)
    """
    # 1. Métricas de chamados por categoria
    chamados_agg = df_chamados.groupby("Tipo de Equipamento").agg(
        Total_Incidentes=("ID do Chamado", "count"),
        Incidentes_Alto_Impacto=("Impacto Causado", lambda x: (x == "Alto").sum()),
        Custo_Total_Estimado=("Custo_Total_Estimado", "sum")
    ).reset_index().rename(columns={"Tipo de Equipamento": "Categoria"})

    # 2. Métricas de inventário por categoria
    inv_agg = df_inventario.groupby("Tipo de equipamento").agg(
        Total_Ativos=("ID do ativo", "count"),
        Ativos_Obsoletos=("Ciclo_Vida", lambda x: (x == "Obsoleto / Vencido").sum()),
        Idade_Media=("Idade de uso (anos)", "mean")
    ).reset_index().rename(columns={"Tipo de equipamento": "Categoria"})

    merged = pd.merge(chamados_agg, inv_agg, on="Categoria", how="outer").fillna(0)

    # Taxas relativas
    merged["Taxa_Alto_Impacto"] = (merged["Incidentes_Alto_Impacto"] / merged["Total_Incidentes"].replace(0, 1)) * 100
    merged["Taxa_Obsolescencia"] = (merged["Ativos_Obsoletos"] / merged["Total_Ativos"].replace(0, 1)) * 100

    # Normalização min-max para cada dimensão (escala 0 a 100)
    def normalize_series(series):
        max_val = series.max()
        min_val = series.min()
        if max_val == min_val:
            return pd.Series(50.0, index=series.index)
        return ((series - min_val) / (max_val - min_val)) * 100

    norm_vol = normalize_series(merged["Total_Incidentes"])
    norm_impact = normalize_series(merged["Taxa_Alto_Impacto"])
    norm_custo = normalize_series(merged["Custo_Total_Estimado"])
    norm_obs = normalize_series(merged["Taxa_Obsolescencia"])

    # Score ponderado
    merged["Score_Atencao"] = (
        norm_vol * 0.30 +
        norm_impact * 0.25 +
        norm_custo * 0.25 +
        norm_obs * 0.20
    ).round(1)

    def nivel_prioridade(score):
        if score >= 70:
            return "Crítica (Ação Imediata)"
        elif score >= 45:
            return "Alta (Acompanhamento)"
        else:
            return "Moderada (Controle de Rotina)"

    merged["Nivel_Prioridade"] = merged["Score_Atencao"].apply(nivel_prioridade)

    return merged.sort_values(by="Score_Atencao", ascending=False)
