"""
Cliente HTTP con retry automático y rate limiting.
Utilidad transversal sin conocimiento de dominio.
"""

import time
import requests
import json
from typing import Optional, Dict, Any, Tuple, List
from datetime import datetime


# Estado global de la sesión (singleton pattern funcional)
_session = None
_last_request_time = 0.0


def create_session(timeout: int = 60) -> requests.Session:
    """
    Crea y retorna una sesión HTTP reutilizable.
    
    Args:
        timeout: Timeout por defecto para las peticiones
        
    Returns:
        requests.Session configurada
    """
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            'User-Agent': 'senv-db-sync/2.0',
            'Accept': 'application/json'
        })
    return _session


def close_session():
    """Cierra la sesión HTTP global si existe."""
    global _session
    if _session:
        _session.close()
        _session = None


def _apply_rate_limit(delay_seconds: float = 0.3):
    """
    Aplica rate limiting entre requests.
    
    Args:
        delay_seconds: Tiempo mínimo entre requests
    """
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < delay_seconds:
        time.sleep(delay_seconds - elapsed)
    _last_request_time = time.time()


def http_get(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 60,
    max_retries: int = 3,
    retry_delay: float = 2.0,
    rate_limit_delay: float = 0.3,
    verbose: bool = True
) -> Tuple[Optional[Any], bool]:
    """
    Realiza GET con retry automático y rate limiting.
    
    Args:
        url: URL completa del endpoint
        params: Query parameters (opcional)
        timeout: Timeout en segundos
        max_retries: Número máximo de reintentos
        retry_delay: Delay base para backoff exponencial
        rate_limit_delay: Delay entre requests para rate limiting
        verbose: Si mostrar logs de progreso
        
    Returns:
        Tupla (datos, éxito)
        - datos: Dict/List con el JSON response o None
        - éxito: True si la petición fue exitosa, False en caso de error
    """
    _apply_rate_limit(rate_limit_delay)
    session = create_session(timeout)
    
    for attempt in range(1, max_retries + 1):
        try:
            response = session.get(url, params=params, timeout=timeout)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return data, True
                except json.JSONDecodeError as e:
                    if verbose:
                        print(f"❌ Error al parsear JSON: {e}")
                    return None, False
            
            elif response.status_code == 404:
                if verbose:
                    print(f"⚠️  Recurso no encontrado (404): {url}")
                return None, True  # No es error, simplemente no hay datos
            
            else:
                if verbose:
                    print(f"⚠️  HTTP {response.status_code} en intento {attempt}/{max_retries}")
        
        except requests.exceptions.Timeout:
            if verbose:
                print(f"⏱️  Timeout en intento {attempt}/{max_retries}")
        
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"❌ Error de conexión en intento {attempt}/{max_retries}: {e}")
        
        # Backoff exponencial antes de reintentar
        if attempt < max_retries:
            wait_time = retry_delay * (2 ** (attempt - 1))
            if verbose:
                print(f"⏳ Reintentando en {wait_time:.1f}s...")
            time.sleep(wait_time)
    
    return None, False


def extract_items_from_response(data: Any) -> list:
    """
    Extrae lista de items de un response de Oracle APEX.
    Maneja múltiples estructuras comunes.
    
    Args:
        data: Response del API (dict o list)
        
    Returns:
        Lista de registros
    """
    if data is None:
        return []
    
    if isinstance(data, list):
        return data
    
    if isinstance(data, dict):
        # Intentar estructuras comunes de Oracle APEX
        for key in ['items', 'rows', 'data']:
            if key in data and isinstance(data[key], list):
                return data[key]
        
        # Si el dict tiene otros campos, puede ser un solo registro
        if data:
            return [data]
    
    return []


def http_get_all_pages(
    url: str,
    initial_params: Optional[Dict[str, Any]] = None,
    limit: int = 1000,
    max_records: Optional[int] = None,
    verbose: bool = True,
    **kwargs
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Obtiene TODAS las páginas de un endpoint paginado automáticamente.
    
    Oracle APEX usa paginación con:
    - hasMore: boolean indicando si hay más páginas
    - offset: desplazamiento actual
    - limit: registros por página
    
    Args:
        url: URL base del endpoint
        initial_params: Parámetros iniciales (opcional)
        limit: Registros por página (default: 1000)
        max_records: Máximo de registros a obtener (None = sin límite)
        verbose: Si mostrar progreso
        **kwargs: Argumentos adicionales para http_get
        
    Returns:
        Tupla (todos_los_registros, éxito)
    """
    all_records = []
    offset = 0
    page = 1
    
    params = initial_params.copy() if initial_params else {}
    params['limit'] = limit
    
    while True:
        params['offset'] = offset
        
        if verbose and page > 1:
            print(f"   📄 Página {page} (offset: {offset})...")
        
        data, success = http_get(url, params=params, verbose=False, **kwargs)
        
        if not success:
            if verbose:
                print(f"❌ Error en página {page}")
            return all_records, False
        
        # Extraer items
        items = extract_items_from_response(data)
        
        if not items:
            # No hay más registros
            break
        
        all_records.extend(items)
        
        if verbose:
            print(f"   ✅ Página {page}: {len(items)} registros (total: {len(all_records):,})")
        
        # Verificar si hay más páginas
        has_more = False
        if isinstance(data, dict):
            has_more = data.get('hasMore', False)
        
        if not has_more:
            # No hay más páginas
            break
        
        # Verificar límite máximo
        if max_records and len(all_records) >= max_records:
            if verbose:
                print(f"⚠️  Límite alcanzado: {max_records:,} registros")
            break
        
        # Avanzar a la siguiente página
        offset += limit
        page += 1
        
        # Seguridad: evitar loops infinitos
        if page > 10000:  # Máximo 10M registros con limit=1000
            if verbose:
                print(f"⚠️  Límite de seguridad alcanzado (página {page})")
            break
    
    return all_records, True
