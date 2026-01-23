"""
Utilidades para manejo de fechas.
Funciones puras sin estado ni dependencias externas.
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple


def parse_oracle_date(date_str: Optional[str]) -> Optional[str]:
    """
    Convierte fechas de Oracle APEX (ISO 8601) a formato PostgreSQL.
    
    Args:
        date_str: Fecha en formato ISO 8601 (ej: "2024-05-30T20:56:43Z")
        
    Returns:
        Fecha en formato PostgreSQL (ej: "2024-05-30 20:56:43") o None
    """
    if not date_str:
        return None
    
    try:
        # Manejar formato ISO 8601 con Z (UTC)
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError):
        return None


def format_date_yyyymmdd(date: datetime) -> str:
    """
    Formatea fecha a YYYYMMDD (usado en endpoints de Oracle APEX).
    
    Args:
        date: Fecha a formatear
        
    Returns:
        String en formato YYYYMMDD (ej: "20260122")
    """
    return date.strftime('%Y%m%d')


def format_date_iso(date: datetime) -> str:
    """
    Formatea fecha a ISO 8601.
    
    Args:
        date: Fecha a formatear
        
    Returns:
        String en formato ISO (ej: "2026-01-22T00:00:00")
    """
    return date.strftime('%Y-%m-%dT%H:%M:%S')


def days_ago(days: int) -> datetime:
    """
    Retorna fecha N días en el pasado desde hoy.
    
    Args:
        days: Número de días hacia atrás
        
    Returns:
        Fecha datetime
    """
    return datetime.now() - timedelta(days=days)


def get_date_range(
    days_back: int = 7,
    end_date: Optional[datetime] = None
) -> Tuple[datetime, datetime]:
    """
    Genera un rango de fechas (inicio, fin).
    
    Args:
        days_back: Días hacia atrás desde end_date
        end_date: Fecha final (default: hoy)
        
    Returns:
        Tupla (fecha_inicio, fecha_fin)
    """
    if end_date is None:
        end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days_back)
    
    return start_date, end_date


def parse_date_flexible(date_str: str) -> datetime:
    """
    Parsea fecha de múltiples formatos comunes.
    
    Args:
        date_str: String con fecha
        
    Returns:
        Objeto datetime
        
    Raises:
        ValueError: Si no se puede parsear la fecha
    """
    formats = [
        '%Y%m%d',           # 20260122
        '%Y-%m-%d',         # 2026-01-22
        '%d/%m/%Y',         # 22/01/2026
        '%d-%m-%Y',         # 22-01-2026
        '%Y-%m-%dT%H:%M:%S',  # ISO 8601
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Formato de fecha no reconocido: {date_str}")
