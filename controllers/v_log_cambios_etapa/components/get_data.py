"""Component: Obtención de datos para v_log_cambios_etapa.

Dos modos de obtención:
- COMPLETO: Endpoint directo /v_log_cambios_etapa (todos los registros, sin filtro)
- INCREMENTAL: Endpoint por orden /periodo/cambios_etapa/{op} iterando sobre órdenes
  obtenidas de log_vidrios_produccion con filtro de fecha.
"""

import os
from typing import List, Dict, Any, Tuple, Optional
from utils.http_client import http_get_all_pages, extract_items_from_response, http_get
from controllers.log_vidrios_produccion.components import get_data as log_vidrios_get_data

BASE_URL = os.getenv('ORACLE_APEX_BASE_URL', 'https://gsn.maxapex.net/apex/savio')
ENDPOINT_PATH = 'periodo/cambios_etapa'
ENDPOINT_PATH_ALL = 'v_log_cambios_etapa'  # Endpoint directo sin filtro


def get_endpoint_url(no_orden_produccion: int) -> str:
    """Construye la URL para una orden de producción específica."""
    return f"{BASE_URL}/{ENDPOINT_PATH}/{no_orden_produccion}"


def get_endpoint_url_all() -> str:
    """Construye la URL del endpoint directo (todos los registros sin filtro)."""
    return f"{BASE_URL}/{ENDPOINT_PATH_ALL}"


def fetch_all_direct(
    timeout: int = 120,
    verbose: bool = True,
    batch_callback=None,
    page_size: int = 1000,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Obtiene TODOS los registros desde /v_log_cambios_etapa con paginación.
    Usar para carga completa histórica (tabla vacía).

    Modo normal (batch_callback=None):
        Acumula todos los registros en memoria y los devuelve.
        Solo viable para datasets pequeños/medianos.

    Modo streaming (batch_callback provisto):
        Llama a batch_callback(batch) por cada página descargada.
        No acumula nada en RAM. Devuelve ([], True) — el total queda
        en manos del caller.
        Firma: batch_callback(records: List[Dict]) -> None

    Args:
        timeout:        Timeout HTTP por página
        verbose:        Mostrar progreso
        batch_callback: Función opcional llamada por cada página
        page_size:      Registros por página (default 1000)
    """
    url = get_endpoint_url_all()
    streaming = batch_callback is not None

    if verbose:
        mode = "streaming (sin acumular en RAM)" if streaming else "acumulando en RAM"
        print(f"📥 Carga completa desde: {url}")
        print(f"   Modo: {mode} | página: {page_size:,} registros")

    all_records = [] if not streaming else None
    offset = 0
    page = 0
    total = 0

    while True:
        page += 1
        params = {'limit': page_size, 'offset': offset}
        data, success = http_get(url, params=params, verbose=False, timeout=timeout)

        if not success or data is None:
            if verbose:
                print(f"❌ Error en página {page} (offset {offset:,})")
            return ([] if not streaming else []), False

        # Extraer items
        if isinstance(data, dict):
            items = data.get('items') or data.get('rows') or data.get('data') or []
            has_more = data.get('hasMore', False)
        elif isinstance(data, list):
            items = data
            has_more = len(items) == page_size
        else:
            break

        if not items:
            break

        total += len(items)

        if verbose and (page == 1 or page % 100 == 0):
            print(f"   📄 Página {page:>6,} | offset {offset:>10,} | "
                  f"esta página: {len(items):,} | total: {total:,}")

        if streaming:
            batch_callback(items)
        else:
            all_records.extend(items)

        if not has_more:
            break

        # Seguridad anti-loop infinito (200M de registros máx a page_size=1000)
        if page >= 200_000:
            if verbose:
                print(f"⚠️  Límite de seguridad alcanzado ({page:,} páginas)")
            break

        offset += page_size

    if verbose:
        print(f"✅ Carga completa: {total:,} registros en {page:,} páginas")

    return (all_records if not streaming else []), True


def get_ordenes_produccion_unicas(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    verbose: bool = True
) -> Tuple[List[int], bool]:
    """
    Obtiene las órdenes de producción únicas de log_vidrios_produccion.
    
    Args:
        fecha_desde: Fecha inicial (YYYY-MM-DD) - opcional
        fecha_hasta: Fecha final (YYYY-MM-DD) - opcional
        verbose: Si mostrar logs
    
    Returns:
        Tupla (lista de órdenes únicas, éxito)
    """
    if verbose:
        if fecha_desde and fecha_hasta:
            print(f"📋 Paso 1: Obteniendo órdenes de log_vidrios_produccion ({fecha_desde} a {fecha_hasta})...")
        else:
            print("📋 Paso 1: Obteniendo órdenes de log_vidrios_produccion (sin filtro)...")
    
    # Obtener logs de vidrios de producción (con filtro de fecha)
    logs, success = log_vidrios_get_data.fetch_all(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        verbose=False
    )
    
    if not success:
        if verbose:
            print("❌ Error al obtener log_vidrios_produccion")
        return [], False
    
    if not logs:
        if verbose:
            print("⚠️  No hay registros en log_vidrios_produccion")
        return [], True
    
    # Extraer órdenes únicas
    ordenes_set = set()
    for log in logs:
        no_orden = log.get('no_orden_produccion') or log.get('NO_ORDEN_PRODUCCION')
        if no_orden:
            ordenes_set.add(int(no_orden))
    
    ordenes_unicas = sorted(list(ordenes_set))
    
    if verbose:
        print(f"   ✅ {len(logs):,} logs → {len(ordenes_unicas):,} órdenes únicas")
    
    return ordenes_unicas, True


def fetch_cambios_for_orden(
    no_orden_produccion: int,
    timeout: int = 60,
    verbose: bool = False
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Obtiene los cambios de etapa para una orden de producción específica.
    
    Args:
        no_orden_produccion: Número de orden de producción
        timeout: Timeout en segundos
        verbose: Si mostrar logs
        
    Returns:
        Tupla (registros, éxito)
    """
    url = get_endpoint_url(no_orden_produccion)
    
    # Obtener datos con paginación
    records, success = http_get_all_pages(
        url,
        limit=1000,
        timeout=timeout,
        verbose=False  # No mostrar progreso individual
    )
    
    return records, success


def fetch_all(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    ordenes_especificas: Optional[List[int]] = None,
    timeout: int = 60,
    verbose: bool = True,
    batch_callback=None,
) -> Tuple[List[Dict[str, Any]], bool]:
    """
    Obtiene todos los cambios de etapa.

    Si no se especifican fechas ni órdenes → usa endpoint directo /v_log_cambios_etapa
    (carga completa histórica, ideal cuando la tabla está vacía).

    Si se especifican fechas → itera por órdenes de log_vidrios_produccion con filtro.

    Args:
        fecha_desde: Fecha inicial (YYYY-MM-DD) para filtrar log_vidrios_produccion
        fecha_hasta: Fecha final (YYYY-MM-DD) para filtrar log_vidrios_produccion
        ordenes_especificas: Lista de órdenes específicas a consultar (opcional)
        timeout: Timeout en segundos
        verbose: Si mostrar logs de progreso

    Returns:
        Tupla (todos los registros, éxito)
    """
    all_records = []

    try:
        # Sin fechas ni órdenes específicas → carga completa directa
        if not fecha_desde and not fecha_hasta and not ordenes_especificas:
            return fetch_all_direct(timeout=timeout, verbose=verbose, batch_callback=batch_callback)

        # Obtener órdenes de producción
        if ordenes_especificas:
            ordenes_unicas = ordenes_especificas
            if verbose:
                print(f"📋 Usando {len(ordenes_unicas):,} órdenes específicas")
        else:
            ordenes_unicas, success = get_ordenes_produccion_unicas(
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
                verbose=verbose
            )
            if not success:
                return [], False
        
        if not ordenes_unicas:
            if verbose:
                print("⚠️  No hay órdenes de producción para consultar")
            return [], True
        
        # Consultar cambios para cada orden
        if verbose:
            print(f"\n📥 Paso 2: Consultando cambios de etapa para {len(ordenes_unicas):,} órdenes...")
        
        total_ordenes = len(ordenes_unicas)
        ordenes_con_cambios = 0
        ordenes_sin_cambios = 0
        ordenes_error = 0
        
        for idx, no_orden in enumerate(ordenes_unicas, 1):
            if verbose and idx % 100 == 0:
                print(f"   Progreso: {idx}/{total_ordenes} órdenes ({ordenes_con_cambios:,} con cambios)")
            
            cambios, success = fetch_cambios_for_orden(no_orden, timeout=timeout, verbose=False)
            
            if success:
                if cambios:
                    all_records.extend(cambios)
                    ordenes_con_cambios += 1
                else:
                    ordenes_sin_cambios += 1
            else:
                ordenes_error += 1
        
        if verbose:
            print(f"\n✅ Proceso completado:")
            print(f"   Total órdenes consultadas: {total_ordenes:,}")
            print(f"   Órdenes con cambios: {ordenes_con_cambios:,}")
            print(f"   Órdenes sin cambios: {ordenes_sin_cambios:,}")
            if ordenes_error > 0:
                print(f"   Órdenes con error: {ordenes_error:,}")
            print(f"   Total registros obtenidos: {len(all_records):,}")
        
        return all_records, True
    
    except Exception as e:
        if verbose:
            print(f"❌ Error al obtener cambios de etapa: {e}")
        return [], False
