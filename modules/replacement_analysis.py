"""
Módulo de análise de substituição vs. manutenção continuada (Trade-off).
Responde à pergunta estratégica: Quando é mais vantajoso substituir um equipamento?
Modela projeções de cenários e ponto de equilíbrio financeiro/operacional.
"""
from typing import Dict, Any
import pandas as pd
from modules.data_loader import load_custos_config

def get_asset_replacement_analysis(df_chamados: pd.DataFrame, df_inventario: pd.DataFrame, limite_pct: float = 0.50) -> pd.DataFrame:
    """
    Consolida o custo acumulado de manutenção por ativo e compara com o valor de aquisição de um novo.
    Identifica ativos que ultrapassaram a linha de corte (trade-off de substituição).
    """
    config_custos = load_custos_config()
    precos_novos = config_custos.get("precos_aquisicao_novo", {})

    # 1. Agregação de chamados por ativo individual
    ativos_manut = df_chamados[df_chamados["ID_Ativo_Extraido"] != "Não Identificado"].groupby("ID_Ativo_Extraido").agg(
        Total_Chamados=("ID do Chamado", "count"),
        Custo_Acumulado_Manutencao=("Custo_Total_Estimado", "sum"),
        Chamados_Alto_Impacto=("Impacto Causado", lambda x: (x == "Alto").sum()),
        Ultimo_Chamado=("Data de Abertura", "max"),
        Primeiro_Chamado=("Data de Abertura", "min"),
        Principais_Defeitos=("Componente_Defeito", lambda x: ", ".join(x.value_counts().head(2).index.tolist()))
    ).reset_index().rename(columns={"ID_Ativo_Extraido": "ID do ativo"})

    # 2. Junção com dados cadastrais do inventário
    df_merged = pd.merge(df_inventario, ativos_manut, on="ID do ativo", how="left")
    df_merged["Total_Chamados"] = df_merged["Total_Chamados"].fillna(0).astype(int)
    df_merged["Custo_Acumulado_Manutencao"] = df_merged["Custo_Acumulado_Manutencao"].fillna(0.0)
    df_merged["Chamados_Alto_Impacto"] = df_merged["Chamados_Alto_Impacto"].fillna(0).astype(int)

    # 3. Determinação do Preço Estimado de um Ativo Novo
    def obter_preco_novo(row):
        cat = str(row.get("Tipo de equipamento", ""))
        modelo = str(row.get("Modelo", ""))
        tabela_cat = precos_novos.get(cat, {})
        if modelo in tabela_cat:
            return float(tabela_cat[modelo])
        return float(tabela_cat.get("padrao", 1000.0))

    df_merged["Preco_Estimado_Novo"] = df_merged.apply(obter_preco_novo, axis=1)

    # 4. Índice de Trade-off (% do valor do novo já gasto em reparos)
    df_merged["Pct_Gasto_Em_Manutencao"] = (
        (df_merged["Custo_Acumulado_Manutencao"] / df_merged["Preco_Estimado_Novo"]) * 100.0
    ).round(1)

    # 5. Recomendação Gerencial Baseada em Regras de Negócio
    def recomendar_acao(row):
        pct_gasto = row["Pct_Gasto_Em_Manutencao"] / 100.0
        ciclo = row.get("Ciclo_Vida", "")
        chamados = row["Total_Chamados"]

        if pct_gasto >= limite_pct or (ciclo == "Obsoleto / Vencido" and chamados >= 2):
            return "Substituir Imediatamente"
        elif pct_gasto >= (limite_pct * 0.70) or ciclo == "Próximo à Obsolescência":
            return "Monitorar / Planejar Troca"
        else:
            return "Manter em Operação"

    df_merged["Recomendacao_Gerencial"] = df_merged.apply(recomendar_acao, axis=1)

    return df_merged.sort_values(by="Pct_Gasto_Em_Manutencao", ascending=False)

def simulate_projection_scenarios(
    df_analysis: pd.DataFrame,
    categoria: str,
    horizonte_meses: int = 24,
    taxa_recorrencia_anual: float = 1.2
) -> Dict[str, Any]:
    """
    Simula e compara dois cenários financeiros para a categoria selecionada:
    Cenário A: Continuar Mantendo (custo cumulativo de reparos + taxa de desgaste)
    Cenário B: Substituição Planejada (aquisição de novo ativo + garantia com custo de manutenção reduzido)
    """
    df_cat = df_analysis[df_analysis["Tipo de equipamento"] == categoria]
    total_ativos = len(df_cat)
    if total_ativos == 0:
        return {}

    custo_medio_novo = df_cat["Preco_Estimado_Novo"].mean()
    custo_medio_manut_ativo = df_cat["Custo_Acumulado_Manutencao"].mean()

    # Custo de substituição (aquisição de novos equipamentos)
    ativos_para_substituir = df_cat[df_cat["Recomendacao_Gerencial"] == "Substituir Imediatamente"]
    qtd_substituir = len(ativos_para_substituir)

    # Projeção mês a mês
    meses = list(range(1, horizonte_meses + 1))
    proj_manutencao = []
    proj_substituicao = []

    # Premissa: custo mensal médio histórico de manutenção por ativo multiplicado pelo fator de desgaste
    custo_manut_mensal_base = (df_cat["Custo_Acumulado_Manutencao"].sum() / 36.0) if len(df_cat) > 0 else 0

    acum_manut = 0.0
    # No cenário de substituição, há um desembolso inicial (CAPEX) para os ativos críticos,
    # mas o custo de manutenção cai para 15% nos ativos novos (garantia)
    capex_inicial = qtd_substituir * custo_medio_novo
    acum_subst = capex_inicial

    for m in meses:
        fator_desgaste = 1.0 + ((m / 12.0) * (taxa_recorrencia_anual - 1.0))
        # Cenário Manter: custos crescem com desgaste do parque
        gasto_mes_manut = custo_manut_mensal_base * fator_desgaste
        acum_manut += gasto_mes_manut
        proj_manutencao.append(acum_manut)

        # Cenário Substituir: economia operacional drástica nos ativos renovados
        gasto_mes_pos_subst = custo_manut_mensal_base * 0.40
        acum_subst += gasto_mes_pos_subst
        proj_substituicao.append(acum_subst)

    df_proj = pd.DataFrame({
        "Mes": meses,
        "Continuar_Mantendo": proj_manutencao,
        "Substituir_Criticos": proj_substituicao
    })

    return {
        "categoria": categoria,
        "total_ativos": total_ativos,
        "qtd_substituir_recomendado": qtd_substituir,
        "capex_aquisicao_novo": capex_inicial,
        "projeção_tabela": df_proj,
        "ponto_equilibrio_mes": next((m for m, man, sub in zip(meses, proj_manutencao, proj_substituicao) if man >= sub), None)
    }
