"""
Controller: Cotizaciones
Orquesta la sincronización desde Oracle APEX a Supabase.
"""

from datetime import datetime
from typing import Dict, Any

from controllers.cotizaciones.components import get_data
from controllers.cotizaciones.components import transform_data
from controllers.cotizaciones.components import synchronize


def sync(verbose: bool = True) -> Dict[str, Any]:
    """
    Función principal de sincronización.
    
    Flujo:
    1. Obtener información previa
    2. Extraer datos del endpoint (con paginación)
    3. Transformar a formato Supabase
    4. Deduplicar
    5. Sincronizar (UPSERT)
    
    Args:
        verbose: Si mostrar logs de progreso
        
    Returns:
        Dict con resultado de la sincronización
    """
    start_time = datetime.now()
    
    result = {
        'controller': 'cotizaciones',
        'success': False,
        'records_fetched': 0,
        'records_synced': 0,
        'fechas_entrega_actualizadas': 0,
        'duration_seconds': 0.0,
        'error': None
    }
    
    try:
        if verbose:
            print("\n" + "="*70)
            print("🔄 CONTROLLER: Cotizaciones")
            print("="*70)
        
        # PASO 1: Información previa
        if verbose:
            print("\n📊 Paso 1/5: Información actual...")
        synchronize.get_last_sync_info(verbose=verbose)
        
        # PASO 2: Extraer datos
        if verbose:
            print("\n📥 Paso 2/5: Extrayendo datos del endpoint...")
        
        records, success = get_data.fetch_all_cotizaciones(verbose=verbose)
        
        if not success:
            result['error'] = "Error al extraer datos del endpoint"
            return result
        
        result['records_fetched'] = len(records)
        
        if not records:
            if verbose:
                print("⚠️  No se obtuvieron registros del endpoint")
            result['success'] = True
            return result
        
        # PASO 3: Transformar
        if verbose:
            print(f"\n🔄 Paso 3/5: Transformando {len(records):,} registros...")
        
        transformed = transform_data.transform_all(records)
        
        if not transformed:
            result['error'] = "Error en transformación"
            return result
        
        # Deduplicar
        unique_records = transform_data.deduplicate_by_id(transformed)
        
        # PASO 4: Sincronizar
        if verbose:
            print(f"\n💾 Paso 4/5: Sincronizando a Supabase...")

        synced_count = synchronize.sync_to_supabase(unique_records, verbose=verbose)

        result['records_synced'] = synced_count

        # PASO 5: Actualizar fecha_entrega_programada desde v_status_pedidos
        if verbose:
            print(f"\n📅 Paso 5/5: Actualizando fechas de entrega programada...")

        status_records, status_ok = get_data.fetch_all_status_pedidos(verbose=verbose)

        if status_ok and status_records:
            fechas_actualizadas = synchronize.sync_fecha_entrega(status_records, verbose=verbose)
            result['fechas_entrega_actualizadas'] = fechas_actualizadas

        result['success'] = True

        duration = (datetime.now() - start_time).total_seconds()
        result['duration_seconds'] = duration

        if verbose:
            print("\n" + "="*70)
            print("✅ COMPLETADO")
            print(f"   📥 Extraídos: {result['records_fetched']:,}")
            print(f"   💾 Sincronizados: {result['records_synced']:,}")
            print(f"   📅 Fechas entrega actualizadas: {result['fechas_entrega_actualizadas']:,}")
            print(f"   ⏱️  Duración: {duration:.1f}s")
            print("="*70)
        
        return result
    
    except Exception as e:
        duration = (datetime.now() - start_time).total_seconds()
        result['duration_seconds'] = duration
        result['error'] = str(e)
        
        if verbose:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
        
        return result


# Alias
run = sync
