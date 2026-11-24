"""
Módulo de registro central de linhagem, governança e catálogo de indicadores.
Fornece metadados vivos sobre a origem, transformação e fórmulas de cada KPI e gráfico do BI.
"""
from typing import Dict, Any, List

METADATA_PAGINAS = {
    "Visão Executiva": {
        "descricao": "Panorama de alto nível para a tomada de decisão rápida da diretoria.",
        "indicadores": [
            {
                "nome": "Total de Chamados",
                "tipo": "KPI",
                "tabelas_origem": ["chamados.xlsx"],
                "colunas_tecnicas": ["ID do Chamado"],
                "modulo_funcao": "modules.incident_analysis.get_general_incident_kpis",
                "formula_leigo": "Contagem de tickets registrados no período após aplicação dos filtros.",
                "formula_tecnica": "df['ID do Chamado'].nunique()"
            },
            {
                "nome": "Custo Estimado de Manutenção",
                "tipo": "KPI",
                "tabelas_origem": ["chamados.xlsx", "config/custos.json"],
                "colunas_tecnicas": ["Subcategoria", "Descrição do Chamado", "Tipo de Equipamento"],
                "modulo_funcao": "modules.cost_analysis.aplicar_custos",
                "formula_leigo": "Soma do valor estimado de peças e mão de obra de todos os reparos.",
                "formula_tecnica": "df['Custo_Total_Estimado'].sum()"
            },
            {
                "nome": "Taxa de Resolução de Chamados",
                "tipo": "KPI",
                "tabelas_origem": ["chamados.xlsx"],
                "colunas_tecnicas": ["Status"],
                "modulo_funcao": "modules.incident_analysis.get_general_incident_kpis",
                "formula_leigo": "Percentual de chamados concluídos em relação ao total recebido.",
                "formula_tecnica": "(df['Status'] == 'Resolvido').sum() / len(df) * 100"
            },
            {
                "nome": "Distribuição de Equipamentos e Incidentes por Categoria",
                "tipo": "Gráfico",
                "tabelas_origem": ["inventario.xlsx", "chamados.xlsx"],
                "colunas_tecnicas": ["Tipo de equipamento (Inventário)", "Tipo de Equipamento (Chamados)"],
                "modulo_funcao": "modules.equipment_analysis.get_equipment_park_distribution",
                "formula_leigo": "Comparação entre o total de ativos existentes no patrimônio e o volume de falhas em campo.",
                "formula_tecnica": "df_inv.groupby('Tipo') vs df_chamados.groupby('Tipo')"
            }
        ]
    },
    "Incidentes": {
        "descricao": "Diagnóstico aprofundado dos sintomas, causas e comparativos temporais.",
        "indicadores": [
            {
                "nome": "Top Sintomas e Subcategorias",
                "tipo": "Gráfico / Tabela",
                "tabelas_origem": ["chamados.xlsx"],
                "colunas_tecnicas": ["Subcategoria", "Resumo do Chamado", "Descrição do Chamado"],
                "modulo_funcao": "modules.incident_analysis.get_incidents_by_category_and_sub",
                "formula_leigo": "Frequência de cada tipo de defeito (ex: tela quebrada, conector, lentidão).",
                "formula_tecnica": "df.groupby(['Tipo de Equipamento', 'Subcategoria']).size()"
            },
            {
                "nome": "Comparativo Temporal (Anual / Mensal / Diário)",
                "tipo": "Comparador A x B",
                "tabelas_origem": ["chamados.xlsx"],
                "colunas_tecnicas": ["Data de Abertura"],
                "modulo_funcao": "modules.incident_analysis.compare_periods",
                "formula_leigo": "Diferença absoluta (Quantidade B − Quantidade A) e variação percentual entre períodos.",
                "formula_tecnica": "Delta_Abs = Qtd_B - Qtd_A; Delta_Pct = ((Qtd_B - Qtd_A) / Qtd_A) * 100"
            }
        ]
    },
    "Equipamentos": {
        "descricao": "Monitoramento da idade, ciclo de vida e priorização de categorias em risco.",
        "indicadores": [
            {
                "nome": "Score Composto de Atenção (Top Categorias)",
                "tipo": "Tabela de Priorização",
                "tabelas_origem": ["chamados.xlsx", "inventario.xlsx", "config/custos.json"],
                "colunas_tecnicas": ["Total_Incidentes", "Impacto Causado", "Custo_Total_Estimado", "Obsolescência"],
                "modulo_funcao": "modules.obsolescence_analysis.calculate_top_attention_categories",
                "formula_leigo": "Pontuação ponderada de 0 a 100 baseada em 4 pilares: Volume (30%), Alto Impacto (25%), Custos (25%) e Obsolescência (20%).",
                "formula_tecnica": "Score = (Norm_Vol * 0.30) + (Norm_Impact * 0.25) + (Norm_Custo * 0.25) + (Norm_Obs * 0.20)"
            },
            {
                "nome": "Situação do Ciclo de Vida do Parque",
                "tipo": "Gráfico de Barras Empilhadas",
                "tabelas_origem": ["inventario.xlsx"],
                "colunas_tecnicas": ["Vida útil (anos)", "Idade de uso (anos)", "Obsolescência"],
                "modulo_funcao": "modules.obsolescence_analysis.get_obsolescence_distribution",
                "formula_leigo": "Ativos classificados em: Dentro da Vida Útil, Próximo à Obsolescência ou Obsoleto/Vencido.",
                "formula_tecnica": "Se Idade >= Vida Útil -> Obsoleto; se Idade >= Vida Útil - 0.5 -> Próximo; senão -> Dentro do prazo"
            }
        ]
    },
    "Ranking": {
        "descricao": "Identificação cirúrgica dos ativos físicos (PB-XXXXX) com maior reincidência de problemas.",
        "indicadores": [
            {
                "nome": "Top 3 Equipamentos Ofensores por Categoria",
                "tipo": "Cards + Histórico",
                "tabelas_origem": ["chamados.xlsx", "inventario.xlsx"],
                "colunas_tecnicas": ["Descrição do Chamado (Regex PB-XXXXX)", "Modelo", "Status"],
                "modulo_funcao": "modules.equipment_analysis.get_top_recurring_equipment_by_category",
                "formula_leigo": "Equipamentos físicos que mais acumularam chamados repetidos na mesma categoria.",
                "formula_tecnica": "df[df['ID_Ativo'] != 'Não Identificado'].groupby('ID_Ativo').size().nlargest(3)"
            }
        ]
    },
    "Custos": {
        "descricao": "Estrutura de custos estimados de manutenção e separação de peças vs. serviços.",
        "indicadores": [
            {
                "nome": "Gasto com Peças vs. Mão de Obra",
                "tipo": "Gráfico de Rosca",
                "tabelas_origem": ["config/custos.json"],
                "colunas_tecnicas": ["Custo_Peca", "Custo_Mao_Obra"],
                "modulo_funcao": "modules.cost_analysis.get_cost_kpis",
                "formula_leigo": "Proporção do valor de manutenção destinado a substituição de componentes físicos vs. mão de obra técnica.",
                "formula_tecnica": "Soma(Custo_Peca) vs Soma(Custo_Mao_Obra)"
            },
            {
                "nome": "Ranking de Custo por Modelo de Dispositivo",
                "tipo": "Tabela de Modelos",
                "tabelas_origem": ["chamados.xlsx", "config/custos.json"],
                "colunas_tecnicas": ["Modelo_Final", "Custo_Total_Estimado"],
                "modulo_funcao": "modules.cost_analysis.get_costs_by_model",
                "formula_leigo": "Modelos que acumularam a maior soma de reparos estimados no período filtrado.",
                "formula_tecnica": "df.groupby('Modelo_Final')['Custo_Total_Estimado'].sum().sort_values(desc)"
            }
        ]
    },
    "Substituição": {
        "descricao": "Avaliação de trade-off financeiro e simulador de ponto de equilíbrio (Break-even).",
        "indicadores": [
            {
                "nome": "Índice de Trade-off de Substituição",
                "tipo": "Gráfico de Dispersão / Tabela",
                "tabelas_origem": ["chamados.xlsx", "inventario.xlsx", "config/custos.json"],
                "colunas_tecnicas": ["Custo_Acumulado_Manutencao", "Preco_Estimado_Novo"],
                "modulo_funcao": "modules.replacement_analysis.get_asset_replacement_analysis",
                "formula_leigo": "Relação percentual entre o quanto já foi gasto em consertos e o valor de um aparelho novo zero km.",
                "formula_tecnica": "(Custo_Acumulado_Manutencao / Preco_Estimado_Novo) * 100 >= Limite_Corte (padrão 50%)"
            },
            {
                "nome": "Projeção de Cenários e Ponto de Equilíbrio",
                "tipo": "Gráfico de Linhas de Projeção",
                "tabelas_origem": ["Simulação Paramétrica"],
                "colunas_tecnicas": ["Custo mensal médio", "Fator de desgaste", "Garantia pós-troca"],
                "modulo_funcao": "modules.replacement_analysis.simulate_projection_scenarios",
                "formula_leigo": "Projeta mês a mês o custo de continuar consertando vs. comprar novo com garantia.",
                "formula_tecnica": "Encontra o mês M onde Custo_Acumulado_Manter >= CAPEX_Novo + Opex_Reduzido"
            }
        ]
    },
    "Impacto Operacional": {
        "descricao": "Disponibilidade de campo, tempos de resolução (MTTR) e SLA nos municípios da PB.",
        "indicadores": [
            {
                "nome": "Tempo Médio de Atendimento (MTTR)",
                "tipo": "KPI / Gráfico",
                "tabelas_origem": ["chamados.xlsx"],
                "colunas_tecnicas": ["Data de Abertura", "Data de Resolução"],
                "modulo_funcao": "modules.operational_impact.get_operational_kpis",
                "formula_leigo": "Média de horas que os chamados levaram entre a abertura no sistema e a solução técnica.",
                "formula_tecnica": "(Data_Resolucao - Data_Abertura).dt.total_seconds() / 3600 -> média"
            },
            {
                "nome": "Cumprimento de SLA",
                "tipo": "KPI",
                "tabelas_origem": ["chamados.xlsx"],
                "colunas_tecnicas": ["Data de Solução Prevista", "Data de Resolução"],
                "modulo_funcao": "modules.operational_impact.get_operational_kpis",
                "formula_leigo": "Percentual de chamados concluídos dentro ou antes do prazo acordado.",
                "formula_tecnica": "(Data_Resolucao <= Data_Solucao_Prevista).sum() / Total * 100"
            }
        ]
    }
}

def get_page_lineage_metadata(page_name: str) -> Dict[str, Any]:
    """Retorna os metadados cadastrados para uma página específica."""
    return METADATA_PAGINAS.get(page_name, {})

def get_data_quality_metrics(df_chamados: Any, df_inventario: Any) -> Dict[str, Any]:
    """
    Calcula indicadores de qualidade do cruzamento sobre o conjunto de dados atual.
    """
    total_chamados = len(df_chamados)
    if total_chamados == 0:
        return {
            "total_chamados": 0,
            "com_ativo_identificado": 0,
            "pct_ativo_identificado": 0.0,
            "casados_inventario": 0,
            "pct_casados_inventario": 0.0,
            "nao_identificados": 0,
            "sem_custo_estimado": 0
        }

    com_ativo = (df_chamados["ID_Ativo_Extraido"] != "Não Identificado").sum()
    nao_identificados = total_chamados - com_ativo
    pct_ativo = (com_ativo / total_chamados) * 100.0

    # Casados com inventário
    casados = df_chamados["ID do ativo"].notna().sum()
    pct_casados = (casados / total_chamados) * 100.0

    # Custos não mapeados ou zero
    sem_custo = (df_chamados["Custo_Total_Estimado"] <= 0).sum()

    return {
        "total_chamados": total_chamados,
        "com_ativo_identificado": int(com_ativo),
        "pct_ativo_identificado": pct_ativo,
        "casados_inventario": int(casados),
        "pct_casados_inventario": pct_casados,
        "nao_identificados": int(nao_identificados),
        "sem_custo_estimado": int(sem_custo)
    }
