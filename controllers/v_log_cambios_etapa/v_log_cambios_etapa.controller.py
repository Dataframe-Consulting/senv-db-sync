"""
Controller: V_Log Cambios Etapa
Orquesta la sincronización desde Oracle APEX a Supabase.

IMPORTANTE: Este controller consulta cambios de etapa basándose en las órdenes
de producción obtenidas de log_vidrios_produccion (con filtro de fecha).
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from controllers.v_log_cambios_etapa.components import get_data
from controllers.v_log_cambios_etapa.components import transform_data
from controllers.v_log_cambios_etapa.components import synchronize


def sync(
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    dias_historico: int = 30,
    full_sync: bool = False,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Función principal de sincronización.
    
    Estrategia inteligente:
    1. Si full_sync=True: sincroniza últimos N días completos (dias_historico)
    2. Si fecha_desde/fecha_hasta: usa esas fechas específicas
    3. Si no: sincronización INCREMENTAL desde última fecha en Supabase
    
    Flujo:
    1. Obtener información previa de Supabase
    2. Determinar rango de fechas (incremental o manual)
    3. Obtener órdenes de log_vidrios_produccion (con filtro de fecha)
    4. Consultar cambios_etapa para cada orden
    5. Transformar a formato Supabase
    6. Deduplicar
    7. Sincronizar (UPSERT)
    
    Args:
        fecha_desde: Fecha inicial (YYYY-MM-DD) - opcional
        fecha_hasta: Fecha final (YYYY-MM-DD) - opcional
        dias_historico: Días hacia atrás si full_sync o no hay datos previos (default: 30)
        full_sync: Si True, fuerza sincronización completa (ignorando fecha en Supabase)
        verbose: Si mostrar logs de progreso
        
    Returns:
        Dict con resultado de la sincronización
    """
    start_time = datetime.now()
    
    result = {
        'controller': 'v_log_cambios_etapa',
        'success': False,
        'records_fetched': 0,
        'records_synced': 0,
        'duration_seconds': 0.0,
        'error': None
    }
    
    try:
        if verbose:
            print("\n" + "="*70)
            print("🔄 CONTROLLER: V_Log Cambios Etapa")
            print("="*70)
        
        # PASO 1: Información previa
        if verbose:
            print("\n📊 Paso 1/5: Información actual...")
        sync_info = synchronize.get_last_sync_info(verbose=verbose)
        
        # PASO 2: Determinar rango de fechas
        if verbose:
            print("\n📅 Paso 2/5: Determinando rango de fechas...")

        # Determinar fecha_desde
        if fecha_desde:
            # Usuario especificó fecha manualmente
            if verbose:
                print(f"   📅 Usando fecha manual: {fecha_desde}")
        elif full_sync:
            # Sincronización completa: últimos N días
            fecha_desde_obj = datetime.now() - timedelta(days=dias_historico)
            fecha_desde = fecha_desde_obj.strftime('%Y-%m-%d')
            if verbose:
                print(f"   🔄 Full sync: últimos {dias_historico} días (desde {fecha_desde})")
        else:
            # Sincronización incremental: desde última fecha en Supabase
            last_modified = sync_info.get('last_modified')
            if last_modified:
                # Usar fecha de última modificación en Supabase
                if 'T' in last_modified:
                    fecha_desde = last_modified.split('T')[0]
                elif ' ' in last_modified:
                    fecha_desde = last_modified.split(' ')[0]
                else:
                    fecha_desde = last_modified
                if verbose:
                    print(f"   ⚡ Sincronización incremental desde última modificación: {fecha_desde}")
            else:
                # Tabla vacía → carga completa sin filtro de fecha
                # Se usará el endpoint general de log_vidrios_produccion (todos los registros)
                fecha_desde = None
                fecha_hasta = None
                if verbose:
                    print("   🆕 Tabla vacía: carga completa histórica (sin filtro de fecha)")

        # Determinar fecha_hasta (solo si no se forzó a None arriba)
        if fecha_desde is not None and not fecha_hasta:
            fecha_hasta = datetime.now().strftime('%Y-%m-%d')

        if verbose:
            if fecha_desde and fecha_hasta:
                print(f"   📅 Rango final: {fecha_desde} → {fecha_hasta}")
            else:
                print("   📅 Rango final: COMPLETO (todos los registros disponibles)")
        
        # PASO 3: Extraer datos
        if verbose:
            print(f"\n📥 Paso 3/5: Extrayendo datos del endpoint...")

        # Carga completa (tabla vacía): modo streaming para no saturar RAM
        is_full_load = (fecha_desde is None and fecha_hasta is None)

        if is_full_load:
            if verbose:
                print("   🏦 Modo STREAMING: transformar + sincronizar por páginas (sin acumular en RAM)")

            total_fetched  = 0
            total_synced   = 0
            total_dupes    = 0

            def process_batch(raw_batch):
                nonlocal total_fetched, total_synced, total_dupes
                total_fetched += len(raw_batch)
                transformed   = transform_data.transform_all(raw_batch)
                unique        = transform_data.deduplicate_by_id(transformed)
                total_dupes  += len(transformed) - len(unique)
                synced        = synchronize.sync_to_supabase(unique, verbose=False)
                total_synced += synced

            _, success = get_data.fetch_all(
                fecha_desde=None,
                fecha_hasta=None,
                verbose=verbose,
                timeout=120,
                batch_callback=process_batch,
            )

            if not success:
                result['error'] = "Error al extraer datos del endpoint"
                return result

            if total_dupes > 0:
                print(f"⚠️  Duplicados exactos removidos: {total_dupes:,}")

            result['records_fetched'] = total_fetched
            result['records_synced']  = total_synced
            result['success'] = True

            duration = (datetime.now() - start_time).total_seconds()
            result['duration_seconds'] = duration

            if verbose:
                print("\n" + "="*70)
                print("✅ COMPLETADO")
                print(f"   📥 Extraídos:    {result['records_fetched']:,}")
                print(f"   💾 Sincronizados: {result['records_synced']:,}")
                print(f"   ⏱️  Duración:    {duration:.1f}s")
                print("="*70)

            return result

        # Modo normal (incremental): acumula en memoria y luego sincroniza
        records, success = get_data.fetch_all(
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            verbose=verbose
        )
        
        if not success:
            result['error'] = "Error al extraer datos del endpoint"
            return result
        
        result['records_fetched'] = len(records)
        
        if not records:
            if verbose:
                print("⚠️  No se obtuvieron registros del endpoint")
            result['success'] = True
            return result
        
        # PASO 4: Transformar
        if verbose:
            print(f"\n🔄 Paso 4/5: Transformando {len(records):,} registros...")
        
        transformed = transform_data.transform_all(records)
        
        if not transformed:
            result['error'] = "Error en transformación"
            return result
        
        # Deduplicar
        unique_records = transform_data.deduplicate_by_id(transformed)
        
        # PASO 5: Sincronizar
        if verbose:
            print(f"\n💾 Paso 5/5: Sincronizando a Supabase...")
        
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
