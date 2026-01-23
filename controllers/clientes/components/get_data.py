"""Component: Obtención de datos para clientes."""

import os
from typing import List, Dict, Any, Tuple
from utils.http_client import http_get_all_pages

BASE_URL = os.getenv('ORACLE_APEX_BASE_URL', 'https://gsn.maxapex.net/apex/savio')
ENDPOINT_PATH = 'clientes'


def get_endpoint_url() -> str:
    return f"{BASE_URL}/{ENDPOINT_PATH}"


def fetch_all_clientes(timeout: int = 60, verbose: bool = True) -> Tuple[List[Dict[str, Any]], bool]:
    """Obtiene todos los clientes del endpoint."""
    url = get_endpoint_url()
    
    if verbose:
        print(f"📥 Consultando: {url}")
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
