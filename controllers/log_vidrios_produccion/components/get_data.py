"""Component: Obtención de datos para log_vidrios_produccion."""

import os
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date
from utils.http_client import http_get_all_pages

BASE_URL = os.getenv('ORACLE_APEX_BASE_URL', 'https://gsn.maxapex.net/apex/savio')
ENDPOINT_PATH_PERIODO = 'periodo/log_vidrios'  # Endpoint con filtro de periodo
ENDPOINT_PATH_ALL = 'log_vidrios_produccion'   # Endpoint sin filtro (todos los registros)


def get_endpoint_url(fecha_desde: Optional[str] = None, fecha_hasta: Optional[str] = None) -> str:
    """
    Construye la URL del endpoint según si hay filtros de fecha.
    
    Si hay fechas: usa endpoint con periodo /periodo/log_vidrios/{YYYYMMDD}/{YYYYMMDD}
    Si no hay fechas: usa endpoint general /log_vidrios_produccion
    """
    if fecha_desde and fecha_hasta:
        # Convertir fechas a formato YYYYMMDD
        try:
            # Intentar parsear como date o datetime
            if isinstance(fecha_desde, str):
                # Puede venir como "YYYY-MM-DD" o "YYYY-MM-DD HH:MM:SS"
                fecha_desde_obj = datetime.fromisoformat(fecha_desde.replace(' ', 'T')).date()
            else:
                fecha_desde_obj = fecha_desde
            
            if isinstance(fecha_hasta, str):
                fecha_hasta_obj = datetime.fromisoformat(fecha_hasta.replace(' ', 'T')).date()
            else:
                fecha_hasta_obj = fecha_hasta
            
            fec1 = fecha_desde_obj.strftime("%Y%m%d")
            fec2 = fecha_hasta_obj.strftime("%Y%m%d")
            
            return f"{BASE_URL}/{ENDPOINT_PATH_PERIODO}/{fec1}/{fec2}"
        except Exception as e:
            print(f"⚠️  Error al parsear fechas: {e}")
            return f"{BASE_URL}/{ENDPOINT_PATH_ALL}"
    
    # Sin filtro de fecha, usar endpoint general
    return f"{BASE_URL}/{ENDPOINT_PATH_ALL}"


def fetch_all(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    timeout: int = 60,
    verbose: bool = True
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Obtiene todos los registros del endpoint.
    
    Args:
        fecha_desde: Fecha desde (formato: YYYY-MM-DD)
        fecha_hasta: Fecha hasta (formato: YYYY-MM-DD)
        timeout: Timeout en segundos
        verbose: Si mostrar logs de progreso
        
    Returns:
        Tupla (registros, éxito)
    
    Ejemplos:
        - fetch_all() -> Todos los registros (sin filtro)
        - fetch_all("2026-01-01", "2026-01-23") -> Solo registros del periodo
    """
    url = get_endpoint_url(fecha_desde, fecha_hasta)
    
    if verbose:
        print(f"📥 Consultando: {url}")
        if fecha_desde and fecha_hasta:
            print(f"   Periodo: {fecha_desde} a {fecha_hasta}")
        else:
            print(f"   Sin filtro de fecha (todos los registros)")
        print(f"   (con paginación automática)")
    
    # Obtener TODAS las páginas automáticamente
    records, success = http_get_all_pages(
        url,
        limit=1000,  # Registros por página
        timeout=timeout,
        verbose=verbose
    )
    
    if not success:
        return [], False
    
    if verbose:
        print(f"✅ Total obtenidos: {len(records):,} registros")
    
    return records, True
