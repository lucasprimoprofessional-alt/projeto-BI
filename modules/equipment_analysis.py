"""
Módulo de análise de equipamentos, relação parque instalado vs. incidentes e taxas de falha.
"""
import pandas as pd

def get_equipment_park_distribution(df_inventario: pd.DataFrame) -> pd.DataFrame:
    """Distribuição do total de equipamentos cadastrados no inventário por tipo/categoria."""
    return df_inventario.groupby("Tipo de equipamento").agg(
        Total_Ativos=("ID do ativo", "count"),
        Em_Operacao=("Status", lambda s: (s == "Em operação").sum()),
        Em_Estoque=("Status", lambda s: (s == "Em estoque").sum()),
        Fora_Operacao=("Status", lambda s: (s == "Fora de operação").sum())
    ).reset_index().rename(columns={"Tipo de equipamento": "Categoria"}).sort_values(by="Total_Ativos", ascending=False)

def get_equipment_incident_ratio(df_chamados: pd.DataFrame, df_inventario: pd.DataFrame) -> pd.DataFrame:
    """Calcula a relação entre volume de equipamentos no inventário e quantidade de incidentes."""
    # Contagem de ativos no inventário
    inv_count = df_inventario.groupby("Tipo de equipamento")["ID do ativo"].count().reset_index().rename(
        columns={"Tipo de equipamento": "Categoria", "ID do ativo": "Total_Equipamentos"}
    )

    # Contagem de incidentes
    inc_count = df_chamados.groupby("Tipo de Equipamento")["ID do Chamado"].count().reset_index().rename(
        columns={"Tipo de Equipamento": "Categoria", "ID do Chamado": "Total_Incidentes"}
    )

    ratio_df = pd.merge(inv_count, inc_count, on="Categoria", how="outer").fillna(0)
    ratio_df["Incidentes_Por_Equipamento"] = (
        ratio_df["Total_Incidentes"] / ratio_df["Total_Equipamentos"].replace(0, 1)
    ).round(2)

    return ratio_df.sort_values(by="Total_Incidentes", ascending=False)

def get_top_recurring_equipment_by_category(df_chamados: pd.DataFrame, categoria: str, top_n: int = 3) -> pd.DataFrame:
    """
    Retorna o Top N de equipamentos com maior quantidade de chamados na categoria selecionada.
    Utiliza o ID do ativo físico (PB-XXXXX) quando identificado.
    """
    df_cat = df_chamados[df_chamados["Tipo de Equipamento"] == categoria]
    # Filtrar registros com ativo identificado
    df_identified = df_cat[df_cat["ID_Ativo_Extraido"] != "Não Identificado"]

    if df_identified.empty:
        # Fallback para Modelo se não houver ativo individual
        return df_cat.groupby("Modelo_Final").agg(
            Total_Chamados=("ID do Chamado", "count"),
            Prioridade_Predominante=("Nível de Prioridade", lambda x: x.mode()[0] if not x.empty else "-"),
            Impacto_Predominante=("Impacto Causado", lambda x: x.mode()[0] if not x.empty else "-")
        ).reset_index().rename(columns={"Modelo_Final": "Equipamento_Modelo"}).sort_values(by="Total_Chamados", ascending=False).head(top_n)

    top_assets = df_identified.groupby(["ID_Ativo_Extraido", "Modelo_Final"]).agg(
        Total_Chamados=("ID do Chamado", "count"),
        Prioridade_Predominante=("Nível de Prioridade", lambda x: x.mode()[0] if not x.empty else "-"),
        Impacto_Predominante=("Impacto Causado", lambda x: x.mode()[0] if not x.empty else "-"),
        Principais_Problemas=("Subcategoria", lambda x: ", ".join(x.value_counts().head(2).index.tolist())),
        Localidades=("Localidade", lambda x: ", ".join(x.unique().tolist()))
    ).reset_index().rename(columns={
        "ID_Ativo_Extraido": "ID_Ativo",
        "Modelo_Final": "Modelo"
    }).sort_values(by="Total_Chamados", ascending=False).head(top_n)

    return top_assets
