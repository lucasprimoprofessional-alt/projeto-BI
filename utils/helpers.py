"""
Módulo de utilidades e formatação para o projeto de BI Energisa Paraíba.
Padronização monetária (R$), datas (DD/MM/AAAA), números compactos e estilos visuais.
"""
from typing import Optional, Union
import pandas as pd

def format_currency_br(value: Optional[Union[int, float]]) -> str:
    """Formata valor numérico para padrão monetário brasileiro R$ 1.234,56."""
    if value is None or pd.isna(value):
        return "R$ 0,00"
    try:
        val_float = float(value)
        formatted = f"{val_float:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted}"
    except (ValueError, TypeError):
        return "R$ 0,00"

def format_currency_compact(value: Optional[Union[int, float]]) -> str:
    """
    Formata valores monetários em formato compacto legível para cartões executivos (KPIs),
    evitando quebras com reticências em telas menores:
    - Ex: R$ 515.820 -> R$ 515,8 mil
    - Ex: R$ 1.250.000 -> R$ 1,3 mi
    - Menor que R$ 10.000 -> R$ 1.234,00
    """
    if value is None or pd.isna(value):
        return "R$ 0,00"
    try:
        val = float(value)
        abs_val = abs(val)
        if abs_val >= 1_000_000:
            formatted = f"{val / 1_000_000:.1f}".replace(".", ",")
            return f"R$ {formatted} mi"
        elif abs_val >= 10_000:
            formatted = f"{val / 1_000:.1f}".replace(".", ",")
            return f"R$ {formatted} mil"
        else:
            return format_currency_br(val)
    except (ValueError, TypeError):
        return "R$ 0,00"

def format_number_br(value: Optional[Union[int, float]], decimals: int = 0) -> str:
    """Formata número com separador de milhar brasileiro."""
    if value is None or pd.isna(value):
        return "0"
    try:
        val_float = float(value)
        if decimals == 0:
            formatted = f"{int(round(val_float)):,}".replace(",", ".")
        else:
            fmt = f"{{:,.{decimals}f}}"
            formatted = fmt.format(val_float).replace(",", "X").replace(".", ",").replace("X", ".")
        return formatted
    except (ValueError, TypeError):
        return "0"

def format_percent_br(value: Optional[Union[int, float]], decimals: int = 1) -> str:
    """Formata valor percentual no padrão brasileiro (ex: 45,2%)."""
    if value is None or pd.isna(value):
        return "0,0%"
    try:
        fmt = f"{{:.{decimals}f}}%"
        return fmt.format(float(value)).replace(".", ",")
    except (ValueError, TypeError):
        return "0,0%"

def format_date_br(dt) -> str:
    """Converte objeto datetime para formato string DD/MM/AAAA."""
    if dt is None or pd.isna(dt):
        return "-"
    try:
        dt = pd.to_datetime(dt)
        return dt.strftime("%d/%m/%Y")
    except Exception:
        return str(dt)

def get_plotly_theme():
    """Retorna paleta de cores corporativa da Energisa para gráficos Plotly."""
    return {
        "primary": "#005596",      # Azul Energisa
        "secondary": "#0083CA",    # Azul Claro
        "accent": "#FF7A00",       # Laranja Corporativo
        "warning": "#D97706",      # Âmbar Alerta (WCAG AA)
        "danger": "#DC2626",       # Vermelho Crítico
        "success": "#16A34A",      # Verde Concluído
        "neutral_dark": "#0F172A", # Slate 900
        "neutral_mid": "#334155",  # Slate 700 (Alto contraste para eixos)
        "neutral_light": "#F8FAFC",# Slate 50
        "border": "#CBD5E1",       # Slate 300
        "palette": ["#005596", "#0083CA", "#FF7A00", "#475569", "#16A34A", "#7C3AED", "#DC2626", "#0D9488"]
    }
