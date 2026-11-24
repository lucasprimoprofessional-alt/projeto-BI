# ⚡ Business Intelligence para Gestão de Ativos e Incidentes
### Energisa Paraíba — Diretoria de TI e Operações de Campo

---

## 1. Visão Geral do Projeto

Este projeto consiste em uma solução profissional de **Business Intelligence (BI) e Analytics**, desenvolvida com **Python, Pandas, Openpyxl, Streamlit e Plotly**, projetada especificamente para apoiar o **Gerente de TI** da Energisa Paraíba na tomada de decisões estratégicas sobre os ativos tecnológicos utilizados pelas equipes de campo (smartphones, tablets, notebooks e impressoras).

A interface foi projetada sob princípios de design de dados minimalista, corporativo e focado na experiência de executivos e gestores não técnicos.

---

## 2. Estrutura de Diretórios e Arquitetura Modular

```text
projeto_bi/
├── app.py                             # Roteamento central com st.navigation, CSS e filtros globais
├── assets/
│   └── style.css                      # Folha de estilos corporativa minimalista (modo normal e apresentação)
├── config/
│   └── custos.json                    # Tabela paramétrica de referência de peças, serviços e aquisições
├── data/
│   ├── chamados.xlsx                  # Base principal de incidentes (2.458 registros no modelo Pós-ETL)
│   └── inventario.xlsx                # Base de inventário patrimonial e ciclo de vida dos equipamentos
├── modules/
│   ├── data_loader.py                 # Leitura com Openpyxl / Pandas com cache (@st.cache_data)
│   ├── data_cleaning.py               # Parsing temporal, extração regex de PB-XXXXX e junções
│   ├── incident_analysis.py           # Agrupamentos, MTTR, SLA e comparativos temporais A x B
│   ├── equipment_analysis.py          # Relação volume vs. incidentes e ranking de reincidência
│   ├── obsolescence_analysis.py       # Ciclo de vida e Score Composto de Atenção (Top Categorias)
│   ├── cost_analysis.py               # Motor de inferência semântica de custos paramétricos
│   ├── replacement_analysis.py        # Modelo de Trade-off (Substituir vs. Manter) e projeção futura
│   └── operational_impact.py          # Indicadores de tempo de atendimento, SLA e impacto regional
├── pages/
│   ├── 1_Visao_Executiva.py           # Painel executivo consolidado com KPIs e gráficos-chave
│   ├── 2_Incidentes.py                # Diagnóstico de falhas e comparativos interativos A x B
│   ├── 3_Equipamentos.py              # Saúde do parque, obsolescência e Score Composto
│   ├── 4_Ranking.py                   # Top 3 equipamentos por categoria e histórico com diálogo modal
│   ├── 5_Custos.py                    # Distribuição de custos (peças, mão de obra e serviços)
│   ├── 6_Substituicao.py              # Análise de substituição vs. manutenção e simulador
│   ├── 7_Impacto_Operacional.py       # Disponibilidade, MTTR, SLA e impacto por município da PB
│   └── 8_Linhagem_Dados.py            # Como os Dados se Cruzam: transparência, qualidade e funil ao vivo
├── utils/
│   ├── helpers.py                     # Formatadores monetários (R$), números e datas BR
│   ├── ui.py                          # Componentes visuais, cards, empty state e template Plotly
│   ├── filters.py                     # Centralização de filtros, estado de sessão e auditoria do funil
│   └── lineage.py                     # Registro central de metadados, fórmulas e linhagem
├── requirements.txt                   # Dependências do projeto (streamlit>=1.40.0)
└── README.md                          # Manual completo do usuário e documentação de governança
```

---

## 3. De Onde Saíram os Dados? (Origem e Governança)

1. **Contexto Operacional:** As equipes de campo da Energisa Paraíba atendem ocorrências emergenciais e manutenções programadas de rede elétrica em todo o estado. Dispositivos móveis inoperantes impedem o recebimento de ordens de serviço e o despacho operacional.
2. **Transformação Pré-ETL (43 campos) para Pós-ETL (15 campos):** A base original do ITSM continha dezenas de colunas técnicas de controle de fila e logs internos. Na etapa de engenharia de dados, foram selecionados os 15 campos essenciais para análise de negócio.
3. **Simulação para Fins Acadêmicos:** Para resguardar a privacidade da empresa e atender às exigências de conformidade com a LGPD, os dados de produção foram anonimizados e substituídos por uma base sintética que reproduz fidedignamente o comportamento do ambiente real.
4. **Custos Paramétricos:** A planilha de ITSM não contém colunas de faturamento contábil. Todos os valores em R$ exibidos no painel são **estimativas paramétricas** calculadas pelo motor do `config/custos.json`, com base nas falhas relatadas.

---

## 4. Como Navegar e Ler o Painel de BI

A barra lateral organiza a navegação em quatro blocos lógicos:

### Bloco A — Visão Geral
* **Visão Executiva:** Leitura em 10 segundos da situação atual. Apresenta 8 KPIs organizados em 2 linhas (Volume/Custos e Criticidade/SLA). Permite **clicar nas barras do gráfico de categorias** para aplicar filtro cruzado (*cross-filtering*) imediato em todo o painel.

### Bloco B — Operação & Ativos
* **Incidentes:** Mostra a frequência de sintomas e subcategorias de defeito com seletor de alternância (*Quantidade de Chamados* ↔ *Custo Estimado*). Na seção inferior, um comparador interativo permite confrontar **dois anos, dois meses ou dois dias** específicos, calculando a variação absoluta e percentual sem recarregar a página.
* **Equipamentos & Obsolescência:** Avalia a saúde do parque e exibe o **Score Composto de Atenção** (ranking das categorias mais críticas baseado em Volume 30%, Alto Impacto 25%, Custos 25% e Obsolescência 20%).
* **Ranking de Reincidência:** Selecione a categoria para visualizar o **Top 3 ativos físicos individuais (PB-XXXXX)** com mais quebras acumuladas. Ao clicar em *"Ver Histórico"*, abre-se uma janela modal (*st.dialog*) com a ficha completa e todas as ordens de serviço do equipamento.
* **Impacto Operacional:** Analisa o tempo médio de resolução (MTTR em horas e dias), a taxa de cumprimento de prazos contratuais (SLA) e a concentração de problemas nos municípios da Paraíba.

### Bloco C — Estratégia & Custos
* **Custos de Manutenção:** Rastreia o valor total estimado e divide claramente os gastos entre **Peças Físicas (Hardware)** e **Mão de Obra Técnica**, ranqueando os modelos mais dispendiosos.
* **Substituição vs. Manutenção:** Responde à pergunta *"Quando substituir um ativo?"*. Apresenta um *slider* de ponto de corte (padrão 50% do valor de um novo) e um **Simulador de Projeção Futura (12, 24 ou 36 meses)** que calcula o mês de *break-even* onde a compra de novos equipamentos empata com a manutenção dos antigos.

### Bloco D — Transparência & Linhagem
* **Como os Dados se Cruzam:** Página dedicada à explicabilidade e auditoria da sessão:
  1. **Integridade ao Vivo:** Percentual de chamados com ativo identificado por regex e casados com o inventário.
  2. **Funil de Filtragem:** Gráfico que mostra exatamente quantos chamados foram removidos por cada filtro ativo na barra lateral.
  3. **Mapa Visual de Cruzamento:** Diagrama das tabelas de entrada e das chaves de junção.
  4. **Dicionário Interativo de Métricas:** Seletor por página que explica a fórmula em linguagem leiga para gestores e em código técnico (via toggle).
  5. **Amostra Viva:** Tabela que confronta os campos da planilha de chamados com os dados herdados do inventário e do JSON.

---

## 5. Como Executar a Aplicação Localmente

### 1. Pré-requisitos
* Python 3.9 a 3.13 instalado.
* Dependências listadas em `requirements.txt`:
  * `streamlit>=1.40.0` (suporte a `st.navigation`, `st.Page`, `st.dialog`, `st.fragment`, `st.segmented_control` e `on_select`)
  * `pandas>=2.0.0`
  * `openpyxl>=3.1.0`
  * `plotly>=5.18.0`

### 2. Instalação e Execução
No terminal (PowerShell ou Prompt de Comando):

```bash
# 1. Navegue até a pasta do projeto
cd "C:\Users\lucas\.gemini\antigravity\scratch\projeto_bi"

# 2. Instale as bibliotecas
pip install -r requirements.txt

# 3. Inicie o dashboard
streamlit run app.py
```

O navegador abrirá automaticamente em `http://localhost:8501`.

---

## 6. Recursos de Navegação

* **Chips de Filtros com Limpeza Rápida:** O topo de cada página exibe os filtros aplicados e permite limpá-los com um único clique.
* **Cross-Filtering:** Clique nas barras do gráfico de categorias na Visão Executiva para filtrar o painel instantaneamente.

---

## 7. Limitações Documentadas

1. **Campos descartados no Pós-ETL:** A base tratada não inclui registros de produtividade por atendente, controle de filas ou canais de abertura de chamados.
2. **Diferença entre MTTR e Indisponibilidade Real:** O tempo de atendimento mede o ciclo de vida do chamado no Service Desk; a indisponibilidade real depende da existência de aparelho reserva na viatura.
3. **Custos Paramétricos:** Todos os valores financeiros são estimativas derivadas da tabela homologada em `config/custos.json`.
