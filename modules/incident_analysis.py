"""
Módulo de análise aprofundada de incidentes e comparativos temporais.
Implementa comparativos interativos anuais, mensais e diários com variações absolutas e percentuais.
"""
from typing import Dict, Any, Tuple
import pandas as pd

def get_general_incident_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    """Calcula os KPIs gerais de incidentes exigidos na Visão Executiva e Análise de Incidentes."""
    total = len(df)
    if total == 0:
        return {
            "total_chamados": 0,
            "resolvidos": 0,
            "pendentes": 0,
            "taxa_resolucao": 0.0,
            "alto_impacto": 0,
            "pct_alto_impacto": 0.0,
            "sla_cumprido_pct": 0.0,
            "mttr_horas": 0.0
        }

    resolvidos = (df["Status"] == "Resolvido").sum()
    pendentes = total - resolvidos
    taxa_res = (resolvidos / total) * 100.0

    alto_impacto = (df["Impacto Causado"] == "Alto").sum()
    pct_alto_impacto = (alto_impacto / total) * 100.0

    sla_cumprido = (~df["SLA_Estourado"]).sum()
    sla_pct = (sla_cumprido / total) * 100.0

    mttr_horas = df["Tempo_Resolucao_Horas"].dropna().mean()

    return {
        "total_chamados": total,
        "resolvidos": int(resolvidos),
        "pendentes": int(pendentes),
        "taxa_resolucao": taxa_res,
        "alto_impacto": int(alto_impacto),
        "pct_alto_impacto": pct_alto_impacto,
        "sla_cumprido_pct": sla_pct,
        "mttr_horas": float(mttr_horas) if not pd.isna(mttr_horas) else 0.0
    }

def get_incidents_by_category_and_sub(df: pd.DataFrame) -> pd.DataFrame:
    """Distribuição por Categoria e Subcategoria."""
    return df.groupby(["Tipo de Equipamento", "Subcategoria"]).agg(
        Total=("ID do Chamado", "count")
    ).reset_index().sort_values(by="Total", ascending=False)

def get_incidents_temporal_series(df: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """Evolução temporal do volume de chamados."""
    df_temp = df.dropna(subset=["Data de Abertura"]).copy()
    if freq == "M":
        return df_temp.groupby("Ano_Mes_Abertura")["ID do Chamado"].count().reset_index().rename(
            columns={"Ano_Mes_Abertura": "Periodo", "ID do Chamado": "Quantidade"}
        )
    elif freq == "Y":
        return df_temp.groupby("Ano_Abertura")["ID do Chamado"].count().reset_index().rename(
            columns={"Ano_Abertura": "Periodo", "ID do Chamado": "Quantidade"}
        )
    else:
        return df_temp.groupby("Data_Abertura_Dia")["ID do Chamado"].count().reset_index().rename(
            columns={"Data_Abertura_Dia": "Periodo", "ID do Chamado": "Quantidade"}
        )

def compare_periods(qty_a: int, qty_b: int) -> Tuple[int, float]:
    """
    Calcula variação absoluta e percentual entre dois períodos:
    Variação Absoluta = Qty_B - Qty_A
    Variação Percentual = ((Qty_B - Qty_A) / Qty_A) * 100
    """
    diff_abs = qty_b - qty_a
    if qty_a > 0:
        diff_pct = (diff_abs / qty_a) * 100.0
    else:
        diff_pct = 100.0 if qty_b > 0 else 0.0
    return diff_abs, diff_pct

def compare_annual(df: pd.DataFrame, year_a: int, year_b: int) -> Dict[str, Any]:
    """Compara dois anos específicos."""
    df_a = df[df["Ano_Abertura"] == year_a]
    df_b = df[df["Ano_Abertura"] == year_b]

    qty_a = len(df_a)
    qty_b = len(df_b)
    diff_abs, diff_pct = compare_periods(qty_a, qty_b)

    by_cat_a = df_a["Tipo de Equipamento"].value_counts().to_dict()
    by_cat_b = df_b["Tipo de Equipamento"].value_counts().to_dict()

    all_cats = list(set(list(by_cat_a.keys()) + list(by_cat_b.keys())))
    cat_comp = []
    for cat in all_cats:
        c_a = by_cat_a.get(cat, 0)
        c_b = by_cat_b.get(cat, 0)
        d_abs, d_pct = compare_periods(c_a, c_b)
        cat_comp.append({
            "Categoria": cat,
            f"Qtd_{year_a}": c_a,
            f"Qtd_{year_b}": c_b,
            "Dif_Absoluta": d_abs,
            "Var_Percentual": d_pct
        })

    return {
        "ano_a": year_a,
        "ano_b": year_b,
        "qtd_a": qty_a,
        "qtd_b": qty_b,
        "diff_abs": diff_abs,
        "diff_pct": diff_pct,
        "tabela_categorias": pd.DataFrame(cat_comp).sort_values(by=f"Qtd_{year_b}", ascending=False)
    }

def compare_monthly(df: pd.DataFrame, month_a: str, month_b: str) -> Dict[str, Any]:
    """Compara dois meses específicos (formato YYYY-MM)."""
    df_a = df[df["Ano_Mes_Abertura"] == month_a]
    df_b = df[df["Ano_Mes_Abertura"] == month_b]

    qty_a = len(df_a)
    qty_b = len(df_b)
    diff_abs, diff_pct = compare_periods(qty_a, qty_b)

    return {
        "mes_a": month_a,
        "mes_b": month_b,
        "qtd_a": qty_a,
        "qtd_b": qty_b,
        "diff_abs": diff_abs,
        "diff_pct": diff_pct
    }

def compare_daily(df: pd.DataFrame, date_a, date_b) -> Dict[str, Any]:
    """Compara dois dias específicos."""
    df_a = df[df["Data_Abertura_Dia"] == date_a]
    df_b = df[df["Data_Abertura_Dia"] == date_b]

    qty_a = len(df_a)
    qty_b = len(df_b)
    diff_abs, diff_pct = compare_periods(qty_a, qty_b)

    return {
        "data_a": str(date_a),
        "data_b": str(date_b),
        "qtd_a": qty_a,
        "qtd_b": qty_b,
        "diff_abs": diff_abs,
        "diff_pct": diff_pct
    }
