"""Component: Sincronización para log_vidrios_produccion."""

from typing import List, Dict, Any
from utils.supabase_client import batch_upsert, get_max_date, count_records

TABLE_NAME = 'log_vidrios_produccion'
CONFLICT_COLUMN = 'id'
BATCH_SIZE = 1000


def sync_to_supabase(records: List[Dict[str, Any]], verbose: bool = True) -> int:
    """Sincroniza registros a Supabase."""
    if not records:
        if verbose:
            print("⚠️  No hay registros para sincronizar")
        return 0
    
    if verbose:
        print(f"💾 Sincronizando {len(records):,} registros...")
    
    try:
        total = batch_upsert(TABLE_NAME, records, CONFLICT_COLUMN, BATCH_SIZE, verbose)
        
        if verbose:
            print(f"✅ Sincronizados: {total:,} registros")
        
        return total
    except Exception as e:
        print(f"❌ Error al sincronizar: {e}")
        raise


def get_last_sync_info(verbose: bool = True) -> Dict[str, Any]:
    """Obtiene información de última sincronización."""
    try:
        total = count_records(TABLE_NAME)
        last_modified = get_max_date(TABLE_NAME, 'fec_modif')
        
        if verbose:
            print(f"📊 Registros actuales: {total:,}")
            if last_modified:
                print(f"📅 Última modificación: {last_modified}")
        
        return {'total_records': total, 'last_modified': last_modified}
    except Exception as e:
        print(f"⚠️  Error obteniendo info: {e}")
        return {'total_records': 0, 'last_modified': None}
