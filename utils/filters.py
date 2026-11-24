"""
Módulo de centralização de filtros, estado global e auditoria do funil de filtragem.
Evita repetição de código nas páginas e alimenta a linhagem de dados.
"""
from typing import Tuple, List, Dict, Any
import pandas as pd
import streamlit as st

def init_filter_state():
    """Garante que as chaves de filtro existam no session_state."""
    defaults = {
        "filter_period": None,
        "filter_tipo": [],
        "filter_prioridade": [],
        "filter_localidade": [],
        "filter_subcat": [],
        "filter_impacto": [],
        "filter_status": [],
        "cross_filter_category": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def reset_filters():
    """Restaura todos os filtros para o padrão original sem desativar o modo apresentação."""
    st.session_state["filter_period"] = None
    st.session_state["filter_tipo"] = []
    st.session_state["filter_prioridade"] = []
    st.session_state["filter_localidade"] = []
    st.session_state["filter_subcat"] = []
    st.session_state["filter_impacto"] = []
    st.session_state["filter_status"] = []
    st.session_state["cross_filter_category"] = None

def render_sidebar_controls(df_all: pd.DataFrame):
    """
    Renderiza os filtros na barra lateral de forma enxuta e organizada.
    Apenas período e 3 filtros principais ficam visíveis; o restante fica em Filtros Avançados.
    """
    init_filter_state()

    with st.sidebar:
        # 1. Identidade Corporativa
        st.markdown("""
        <div style="padding: 0.5rem 0 1rem 0; border-bottom: 1px solid #E2E8F0; margin-bottom: 1rem;">
            <div style="font-size: 1.15rem; font-weight: 800; color: #005596; letter-spacing: -0.02em;">⚡ ENERGISA</div>
            <div style="font-size: 0.8rem; color: #475569; font-weight: 600;">Gestão de Ativos & Suporte TI</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### Filtros Principais")

        # Filtro de Período
        min_date = df_all["Data_Abertura_Dia"].min()
        max_date = df_all["Data_Abertura_Dia"].max()
        
        val_period = st.session_state["filter_period"]
        if not val_period or not isinstance(val_period, tuple) or len(val_period) != 2:
            val_period = (min_date, max_date)

        st.session_state["filter_period"] = st.date_input(
            "Período de Abertura:",
            value=val_period,
            min_value=min_date,
            max_value=max_date,
            format="DD/MM/YYYY"
        )

        # Categoria do Equipamento
        cats_disponiveis = sorted(df_all["Tipo de Equipamento"].dropna().unique().tolist())
        st.session_state["filter_tipo"] = st.multiselect(
            "Categoria do Equipamento:",
            options=cats_disponiveis,
            default=st.session_state["filter_tipo"]
        )

        # Prioridade
        prioridades = sorted(df_all["Nível de Prioridade"].dropna().unique().tolist())
        st.session_state["filter_prioridade"] = st.multiselect(
            "Nível de Prioridade:",
            options=prioridades,
            default=st.session_state["filter_prioridade"]
        )

        # Localidade
        localidades = sorted(df_all["Localidade"].dropna().unique().tolist())
        st.session_state["filter_localidade"] = st.multiselect(
            "Localidade (PB):",
            options=localidades,
            default=st.session_state["filter_localidade"]
        )

        # Filtros Avançados em Expander
        with st.expander("Filtros Avançados", expanded=False):
            subcats = sorted(df_all["Subcategoria"].dropna().unique().tolist())
            st.session_state["filter_subcat"] = st.multiselect(
                "Subcategoria / Defeito:",
                options=subcats,
                default=st.session_state["filter_subcat"]
            )

            impactos = sorted(df_all["Impacto Causado"].dropna().unique().tolist())
            st.session_state["filter_impacto"] = st.multiselect(
                "Impacto Causado:",
                options=impactos,
                default=st.session_state["filter_impacto"]
            )

            status_list = sorted(df_all["Status"].dropna().unique().tolist())
            st.session_state["filter_status"] = st.multiselect(
                "Status do Chamado:",
                options=status_list,
                default=st.session_state["filter_status"]
            )

        if st.button("Limpar todos os filtros", use_container_width=True):
            reset_filters()
            st.rerun()

def apply_filters(df_all: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, str]], List[Dict[str, Any]]]:
    """
    Aplica os filtros de forma encadeada, rastreando a auditoria do funil passo a passo.
    Retorna: (DataFrame Filtrado, Lista de Chips Ativos, Histórico do Funil)
    """
    init_filter_state()
    df = df_all.copy()
    
    total_inicial = len(df)
    funil_audit = [
        {"etapa": "Base Total", "registros": total_inicial, "removidos": 0, "filtro_ativo": True}
    ]
    active_chips = []

    # 1. Período
    periodo = st.session_state.get("filter_period")
    if isinstance(periodo, tuple) and len(periodo) == 2:
        d_start, d_end = periodo
        qtd_antes = len(df)
        df = df[(df["Data_Abertura_Dia"] >= d_start) & (df["Data_Abertura_Dia"] <= d_end)]
        removidos = qtd_antes - len(df)
        is_ativo = (d_start > df_all["Data_Abertura_Dia"].min() or d_end < df_all["Data_Abertura_Dia"].max())
        if is_ativo:
            active_chips.append({"label": "Período", "value": f"{d_start.strftime('%d/%m/%y')} a {d_end.strftime('%d/%m/%y')}"})
        funil_audit.append({"etapa": "Filtro de Período", "registros": len(df), "removidos": removidos, "filtro_ativo": is_ativo})

    # 2. Categoria
    tipos = st.session_state.get("filter_tipo", [])
    if tipos:
        qtd_antes = len(df)
        df = df[df["Tipo de Equipamento"].isin(tipos)]
        removidos = qtd_antes - len(df)
        active_chips.append({"label": "Categoria", "value": ", ".join(tipos)})
        funil_audit.append({"etapa": "Categoria Equipamento", "registros": len(df), "removidos": removidos, "filtro_ativo": True})
    else:
        funil_audit.append({"etapa": "Categoria Equipamento", "registros": len(df), "removidos": 0, "filtro_ativo": False})

    # 3. Prioridade
    prioridades = st.session_state.get("filter_prioridade", [])
    if prioridades:
        qtd_antes = len(df)
        df = df[df["Nível de Prioridade"].isin(prioridades)]
        removidos = qtd_antes - len(df)
        active_chips.append({"label": "Prioridade", "value": ", ".join(prioridades)})
        funil_audit.append({"etapa": "Nível Prioridade", "registros": len(df), "removidos": removidos, "filtro_ativo": True})
    else:
        funil_audit.append({"etapa": "Nível Prioridade", "registros": len(df), "removidos": 0, "filtro_ativo": False})

    # 4. Localidade
    localidades = st.session_state.get("filter_localidade", [])
    if localidades:
        qtd_antes = len(df)
        df = df[df["Localidade"].isin(localidades)]
        removidos = qtd_antes - len(df)
        active_chips.append({"label": "Localidade", "value": f"{len(localidades)} cidade(s)" if len(localidades) > 2 else ", ".join(localidades)})
        funil_audit.append({"etapa": "Localidade (PB)", "registros": len(df), "removidos": removidos, "filtro_ativo": True})
    else:
        funil_audit.append({"etapa": "Localidade (PB)", "registros": len(df), "removidos": 0, "filtro_ativo": False})

    # 5. Subcategoria
    subcats = st.session_state.get("filter_subcat", [])
    if subcats:
        qtd_antes = len(df)
        df = df[df["Subcategoria"].isin(subcats)]
        removidos = qtd_antes - len(df)
        active_chips.append({"label": "Subcategoria", "value": ", ".join(subcats)})
        funil_audit.append({"etapa": "Subcategoria", "registros": len(df), "removidos": removidos, "filtro_ativo": True})
    else:
        funil_audit.append({"etapa": "Subcategoria", "registros": len(df), "removidos": 0, "filtro_ativo": False})

    # 6. Impacto
    impactos = st.session_state.get("filter_impacto", [])
    if impactos:
        qtd_antes = len(df)
        df = df[df["Impacto Causado"].isin(impactos)]
        removidos = qtd_antes - len(df)
        active_chips.append({"label": "Impacto", "value": ", ".join(impactos)})
        funil_audit.append({"etapa": "Impacto Causado", "registros": len(df), "removidos": removidos, "filtro_ativo": True})
    else:
        funil_audit.append({"etapa": "Impacto Causado", "registros": len(df), "removidos": 0, "filtro_ativo": False})

    # 7. Status
    status_sel = st.session_state.get("filter_status", [])
    if status_sel:
        qtd_antes = len(df)
        df = df[df["Status"].isin(status_sel)]
        removidos = qtd_antes - len(df)
        active_chips.append({"label": "Status", "value": ", ".join(status_sel)})
        funil_audit.append({"etapa": "Status", "registros": len(df), "removidos": removidos, "filtro_ativo": True})
    else:
        funil_audit.append({"etapa": "Status", "registros": len(df), "removidos": 0, "filtro_ativo": False})

    # 8. Cross-Filtering Interativo em Gráfico
    cross_cat = st.session_state.get("cross_filter_category")
    if cross_cat:
        qtd_antes = len(df)
        df = df[df["Tipo de Equipamento"] == cross_cat]
        removidos = qtd_antes - len(df)
        active_chips.append({"label": "Filtro no Gráfico", "value": f"Categoria: {cross_cat}"})
        funil_audit.append({"etapa": f"Interação em Gráfico ({cross_cat})", "registros": len(df), "removidos": removidos, "filtro_ativo": True})

    return df, active_chips, funil_audit
