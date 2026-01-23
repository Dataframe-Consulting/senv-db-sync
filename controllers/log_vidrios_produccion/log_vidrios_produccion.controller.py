"""
Controller: Log Vidrios Producción
Orquesta la sincronización desde Oracle APEX a Supabase.

⚠️  IMPORTANTE: Este controller maneja un volumen masivo de datos (265,000+ registros históricos).
Por defecto usa SINCRONIZACIÓN INCREMENTAL para evitar timeouts.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from controllers.log_vidrios_produccion.components import get_data
from controllers.log_vidrios_produccion.components import transform_data
from controllers.log_vidrios_produccion.components import synchronize


def sync(
    verbose: bool = True,
    fecha_desde: Optional[str] = None,
    fecha_hasta: Optional[str] = None,
    full_sync: bool = False,
    dias_historico: int = 30
) -> Dict[str, Any]:
    """
    Función principal de sincronización con soporte incremental.
    
    Flujo:
    1. Obtener información previa y última fecha sincronizada
    2. Determinar rango de fechas (incremental o completo)
    3. Extraer datos del endpoint con filtro de fecha
    4. Transformar a formato Supabase
    5. Deduplicar
    6. Sincronizar (UPSERT)
    
    Args:
        verbose: Si mostrar logs de progreso
        fecha_desde: Fecha desde (formato YYYY-MM-DD). Si no se especifica, usa sincronización incremental
        fecha_hasta: Fecha hasta (formato YYYY-MM-DD). Si no se especifica, usa fecha actual
        full_sync: Si True, sincroniza TODOS los registros históricos (⚠️ puede tomar mucho tiempo)
        dias_historico: Si no hay última fecha en Supabase, sincronizar últimos N días
        
    Returns:
        Dict con resultado de la sincronización
        
    Ejemplos:
        sync()                                    # Sincronización incremental (desde última fecha)
        sync(fecha_desde='2026-01-01')           # Desde fecha específica hasta hoy
        sync(fecha_desde='2026-01-01', fecha_hasta='2026-01-23')  # Rango específico
        sync(full_sync=True)                     # ⚠️ Carga completa (todos los registros)
        sync(dias_historico=7)                   # Últimos 7 días si no hay datos previos
    """
    start_time = datetime.now()
    
    result = {
        'controller': 'log_vidrios_produccion',
        'sync_type': 'unknown',
        'fecha_desde': None,
        'fecha_hasta': None,
        'success': False,
        'records_fetched': 0,
        'records_synced': 0,
        'duration_seconds': 0.0,
        'error': None
    }
    
    try:
        if verbose:
            print("\n" + "="*70)
            print("🔄 CONTROLLER: Log Vidrios Producción (Sincronización Inteligente)")
            print("="*70)
        
        # PASO 1: Información previa y determinar rango de fechas
        if verbose:
            print("\n📊 Paso 1/5: Obteniendo información actual...")
        
        sync_info = synchronize.get_last_sync_info(verbose=verbose)
        
        # Determinar fecha_hasta
        if not fecha_hasta:
            fecha_hasta = datetime.now().strftime('%Y-%m-%d')
        
        # Determinar fecha_desde (sincronización incremental)
        if not full_sync:
            if not fecha_desde:
                # Sincronización incremental: usar última fecha de Supabase
                last_modified = sync_info.get('last_modified')
                if last_modified:
                    # Usar la última fecha de modificación
                    if isinstance(last_modified, str):
                        fecha_desde = last_modified.split()[0]  # Tomar solo la parte de fecha
                    else:
                        fecha_desde = last_modified.strftime('%Y-%m-%d')
                    result['sync_type'] = 'incremental'
                    if verbose:
                        print(f"📅 Sincronización INCREMENTAL desde: {fecha_desde}")
                else:
                    # Primera sincronización: usar últimos N días
                    fecha_desde_obj = datetime.now() - timedelta(days=dias_historico)
                    fecha_desde = fecha_desde_obj.strftime('%Y-%m-%d')
                    result['sync_type'] = 'initial'
                    if verbose:
                        print(f"📅 Primera sincronización: últimos {dias_historico} días desde {fecha_desde}")
            else:
                result['sync_type'] = 'custom_range'
                if verbose:
                    print(f"📅 Rango personalizado: {fecha_desde} a {fecha_hasta}")
        else:
            # Sincronización completa (sin filtro de fecha)
            fecha_desde = None
            fecha_hasta = None
            result['sync_type'] = 'full'
            if verbose:
                print("⚠️  Sincronización COMPLETA (todos los registros históricos)")
                print("   Esto puede tomar varios minutos...")
        
        result['fecha_desde'] = fecha_desde
        result['fecha_hasta'] = fecha_hasta
        
        # PASO 2: Extraer datos
        if verbose:
            print(f"\n📥 Paso 2/5: Extrayendo datos del endpoint...")
        
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
        
        # PASO 3: Transformar
        if verbose:
            print(f"\n🔄 Paso 3/5: Transformando {len(records):,} registros...")
        
        transformed = transform_data.transform_all(records)
        
        if not transformed:
            result['error'] = "Error en transformación"
            return result
        
        # PASO 4: Deduplicar
        if verbose:
            print(f"\n✨ Paso 4/5: Deduplicando registros...")
        
        unique_records = transform_data.deduplicate_by_id(transformed)
        
        if verbose:
            duplicados = len(transformed) - len(unique_records)
            if duplicados > 0:
                print(f"   Duplicados removidos: {duplicados:,}")
            print(f"   Registros únicos: {len(unique_records):,}")
        
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
            print(f"   Tipo: {result['sync_type'].upper()}")
            if result['fecha_desde']:
                print(f"   Periodo: {result['fecha_desde']} a {result['fecha_hasta']}")
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
