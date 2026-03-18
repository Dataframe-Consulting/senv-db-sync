"""
Component: Sincronización (persistencia) para cotizaciones.
Maneja la inserción/actualización en Supabase.
"""

from typing import List, Dict, Any
from utils.supabase_client import batch_upsert, get_max_date, count_records


# Configuración específica de este controller
TABLE_NAME = 'cotizaciones'
CONFLICT_COLUMN = 'id'  # Campo para UPSERT (PK)
BATCH_SIZE = 1000


def sync_to_supabase(
    records: List[Dict[str, Any]],
    verbose: bool = True
) -> int:
    """
    Sincroniza registros a Supabase usando UPSERT.
    
    Args:
        records: Lista de registros transformados
        verbose: Si mostrar progreso
        
    Returns:
        Número de registros insertados/actualizados
        
    Raises:
        Exception: Si hay error en la inserción
    """
    if not records:
        if verbose:
            print("⚠️  No hay registros para sincronizar")
        return 0
    
    if verbose:
        print(f"💾 Sincronizando {len(records):,} registros a Supabase...")
    
    try:
        total_synced = batch_upsert(
            table_name=TABLE_NAME,
            records=records,
            conflict_column=CONFLICT_COLUMN,
            batch_size=BATCH_SIZE,
            verbose=verbose
        )
        
        if verbose:
            print(f"✅ Sincronizados: {total_synced:,} registros")
        
        return total_synced
    
    except Exception as e:
        print(f"❌ Error al sincronizar a Supabase: {e}")
        raise


def sync_fecha_entrega(
    status_records: List[Dict[str, Any]],
    verbose: bool = True
) -> int:
    """
    Actualiza fecha_entrega_programada en cotizaciones a partir de los registros
    de v_status_pedidos. Solo procesa registros con fec_prog_entrega no nulo.

    Args:
        status_records: Registros crudos de v_status_pedidos
        verbose: Si mostrar progreso

    Returns:
        Número de registros actualizados
    """
    from controllers.cotizaciones.components.transform_data import parse_oracle_date

    updates = []
    for r in status_records:
        no_cot = r.get('no_cotizacion')
        fec = r.get('fec_prog_entrega')
        if no_cot and fec:
            updates.append({
                'id': str(no_cot),
                'fecha_entrega_programada': parse_oracle_date(fec),
            })

    if not updates:
        if verbose:
            print("⚠️  No hay fechas de entrega para actualizar")
        return 0

    # Deduplicar: si hay varios pedidos del mismo no_cotizacion, tomar el último
    unique = {u['id']: u for u in updates}
    updates = list(unique.values())

    if verbose:
        print(f"💾 Actualizando fecha_entrega_programada en {len(updates):,} cotizaciones...")

    updated = batch_upsert(
        table_name=TABLE_NAME,
        records=updates,
        conflict_column='id',
        batch_size=BATCH_SIZE,
        verbose=verbose
    )

    if verbose:
        print(f"✅ Fechas de entrega actualizadas: {updated:,}")

    return updated


def get_last_sync_info(verbose: bool = True) -> Dict[str, Any]:
    """
    Obtiene información de la última sincronización.
    
    Args:
        verbose: Si mostrar información
        
    Returns:
        Dict con información:
        - total_records: Número total de registros en Supabase
        - last_modified: Última fecha de modificación
    """
    try:
        total = count_records(TABLE_NAME)
        last_modified = get_max_date(TABLE_NAME, 'fec_modif')
        
        info = {
            'total_records': total,
            'last_modified': last_modified
        }
        
        if verbose:
            print(f"📊 Registros en Supabase: {total:,}")
            if last_modified:
                print(f"📅 Última modificación: {last_modified}")
        
        return info
    
    except Exception as e:
        print(f"⚠️  Error al obtener info de última sync: {e}")
        return {
            'total_records': 0,
            'last_modified': None
        }
