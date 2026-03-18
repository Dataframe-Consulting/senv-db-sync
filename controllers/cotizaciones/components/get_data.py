"""
Component: Obtención de datos para cotizaciones.
Define la URL y lógica de extracción específica del endpoint.
"""

import os
from typing import List, Dict, Any, Tuple
from utils.http_client import http_get, extract_items_from_response


# URL del endpoint (configuración específica de este controller)
BASE_URL = os.getenv(
    'ORACLE_APEX_BASE_URL',
    'https://gsn.maxapex.net/apex/savio'
)
ENDPOINT_PATH = 'cotizaciones'


def get_endpoint_url() -> str:
    """
    Retorna la URL completa del endpoint.
    
    Returns:
        URL del endpoint de cotizaciones
    """
    return f"{BASE_URL}/{ENDPOINT_PATH}"


def fetch_all_cotizaciones(
    timeout: int = 60,
    verbose: bool = True
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Obtiene todas las cotizaciones del endpoint con paginación automática.
    
    IMPORTANTE: 
    - Este endpoint NO soporta filtrado por fecha
    - Oracle APEX usa paginación (limit/offset/hasMore)
    - Esta función maneja automáticamente todas las páginas
    
    Args:
        timeout: Timeout en segundos
        verbose: Si mostrar logs de progreso
        
    Returns:
        Tupla (registros, éxito)
        - registros: Lista de cotizaciones (TODAS las páginas)
        - éxito: True si la petición fue exitosa
    """
    url = get_endpoint_url()
    
    if verbose:
        print(f"📥 Consultando: {url}")
        print(f"   (con paginación automática)")
    
    # Importar la función de paginación
    from utils.http_client import http_get_all_pages
    
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


# URL del endpoint de status de pedidos
ENDPOINT_PATH_STATUS = 'v_status_pedidos'


def fetch_all_status_pedidos(
    timeout: int = 60,
    verbose: bool = True
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Obtiene todos los registros de v_status_pedidos con paginación automática.
    Solo se usa para extraer fec_prog_entrega por no_cotizacion.
    """
    url = f"{BASE_URL}/{ENDPOINT_PATH_STATUS}"

    if verbose:
        print(f"📥 Consultando: {url}")
        print(f"   (con paginación automática)")

    from utils.http_client import http_get_all_pages

    records, success = http_get_all_pages(
        url,
        limit=1000,
        timeout=timeout,
        verbose=verbose
    )

    if not success:
        return [], False

    if verbose:
        print(f"✅ Total obtenidos: {len(records):,} registros de status_pedidos")

    return records, True
