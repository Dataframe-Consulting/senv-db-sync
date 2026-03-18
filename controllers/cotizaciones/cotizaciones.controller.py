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
            print("\n📊 Paso 1/4: Información actual...")
        synchronize.get_last_sync_info(verbose=verbose)
        
        # PASO 2: Extraer fechas de entrega desde v_status_pedidos
        if verbose:
            print("\n📅 Paso 2/4: Obteniendo fechas de entrega programada...")

        status_records, _ = get_data.fetch_all_status_pedidos(verbose=verbose)
        fechas_entrega = transform_data.build_fechas_entrega_lookup(status_records)

        if verbose:
            print(f"   📅 Fechas disponibles: {len(fechas_entrega):,}")

        # PASO 3: Extraer cotizaciones
        if verbose:
            print("\n📥 Paso 3/4: Extrayendo cotizaciones del endpoint...")

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

        # PASO 4: Transformar (enriqueciendo con fechas) y sincronizar
        if verbose:
            print(f"\n🔄 Paso 4/4: Transformando y sincronizando {len(records):,} registros...")

        transformed = transform_data.transform_all(records, fechas_entrega)

        if not transformed:
            result['error'] = "Error en transformación"
            return result

        unique_records = transform_data.deduplicate_by_id(transformed)

        synced_count = synchronize.sync_to_supabase(unique_records, verbose=verbose)

        result['records_synced'] = synced_count
        result['success'] = True

        duration = (datetime.now() - start_time).total_seconds()
        result['duration_seconds'] = duration

        if verbose:
            print("\n" + "="*70)
            print("✅ COMPLETADO")
            print(f"   📥 Extraídos: {result['records_fetched']:,}")
            print(f"   💾 Sincronizados: {result['records_synced']:,}")
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
