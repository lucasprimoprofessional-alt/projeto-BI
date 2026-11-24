"""
Módulo de carregamento de dados para o projeto de BI Energisa Paraíba.
Suporta leitura com Openpyxl (arquivos .xlsx) e fallback para CSV.
"""
import os
import json
from pathlib import Path
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"

@st.cache_data(show_spinner="Carregando base de chamados...")
def load_chamados_raw() -> pd.DataFrame:
    """Carrega a base de chamados de incidentes (prioriza .xlsx, fallback para .csv)."""
    xlsx_path = DATA_DIR / "chamados.xlsx"
    csv_path = DATA_DIR / "chamados.csv"

    if xlsx_path.exists():
        try:
            return pd.read_excel(xlsx_path, engine="openpyxl")
        except Exception:
            pass

    if csv_path.exists():
        return pd.read_csv(csv_path, encoding="utf-8")

    raise FileNotFoundError("Base de chamados não encontrada na pasta data/ (chamados.xlsx ou chamados.csv).")

@st.cache_data(show_spinner="Carregando inventário de ativos...")
def load_inventario_raw() -> pd.DataFrame:
    """Carrega a base de inventário de equipamentos (prioriza .xlsx, fallback para .csv)."""
    xlsx_path = DATA_DIR / "inventario.xlsx"
    csv_path = DATA_DIR / "inventario.csv"

    if xlsx_path.exists():
        try:
            return pd.read_excel(xlsx_path, engine="openpyxl")
        except Exception:
            pass

    if csv_path.exists():
        return pd.read_csv(csv_path, encoding="utf-8")

    raise FileNotFoundError("Base de inventário não encontrada na pasta data/ (inventario.xlsx ou inventario.csv).")

@st.cache_data
def load_custos_config() -> dict:
    """Carrega a tabela paramétrica de custos do arquivo JSON externo."""
    json_path = CONFIG_DIR / "custos.json"
    if not json_path.exists():
        raise FileNotFoundError(f"Arquivo de custos não encontrado em {json_path}")
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
