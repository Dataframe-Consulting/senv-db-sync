#!/usr/bin/env python3
"""
Script Principal de Sincronización.

Ejecuta la sincronización de todos los endpoints llamando
explícitamente a cada controller.

Para habilitar/deshabilitar un controller: comentar/descomentar su línea.
"""

import sys
import os
from datetime import datetime

# Añadir el directorio actual al path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()


# =============================================================================
# IMPORTAR CONTROLLERS
# =============================================================================

from controllers import cotizaciones
from controllers import clientes
from controllers import proyectos_cliente
from controllers import v_insumos
from controllers import detalle_cotizacion
from controllers import vidrios_produccion
from controllers import log_vidrios_produccion
from controllers import v_log_cambios_etapa


# =============================================================================
# FUNCIÓN PRINCIPAL
# =============================================================================

def main():
    """
    Ejecuta la sincronización de todos los controllers.
    
    Para habilitar/deshabilitar un controller:
    - Comentar la línea para deshabilitarlo
    - Descomentar la línea para habilitarlo
    
    Controllers por volumen de datos:
    - Rápidos (<5s): clientes, proyectos_cliente, v_insumos, cotizaciones
    - Medios (5-20s): detalle_cotizacion
    - Grandes (>1min): vidrios_produccion, log_vidrios_produccion, v_log_cambios_etapa
    """
    start_time = datetime.now()
    
    print("\n" + "="*80)
    print("🚀 SINCRONIZACIÓN ERP → SUPABASE")
    print("="*80)
    print(f"⏰ Iniciado: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Verificar variables de entorno
    if not os.getenv('SUPABASE_URL') or not os.getenv('SUPABASE_KEY'):
        print("❌ ERROR: Faltan variables de entorno SUPABASE_URL y/o SUPABASE_KEY")
        return 1
    
    # Lista para recopilar resultados
    results = []
    
    try:
        # =================================================================
        # EJECUTAR CADA CONTROLLER EXPLÍCITAMENTE
        # Para deshabilitar un controller: comentar su línea con #
        # =================================================================
        
        # ========== CONTROLLERS RÁPIDOS (Catálogos y Maestros) ==========
        print("\n📦 Sincronizando catálogos maestros...")
        results.append(clientes.run())              # ~36 registros, <1s
        results.append(proyectos_cliente.run())     # ~231 registros, <1s
        results.append(v_insumos.run())             # ~249 registros, <1s
        
        # ========== CONTROLLERS MEDIOS (Transaccionales) ==========
        print("\n📋 Sincronizando datos transaccionales...")
        results.append(cotizaciones.run())          # ~2K registros, ~3s
        results.append(detalle_cotizacion.run())    # ~18K registros, ~12s
        
        # ========== CONTROLLERS GRANDES (Producción) ==========
        print("\n🏭 Sincronizando datos de producción...")
        results.append(vidrios_produccion.run())    # ~98K registros, ~80s
        
        # ⚠️ IMPORTANTE: log_vidrios_produccion usa sincronización INCREMENTAL
        # Solo sincroniza cambios desde la última ejecución (mucho más rápido)
        results.append(log_vidrios_produccion.run())  # Incremental: ~15K registros, ~5s
        
        # ⚠️ ADVERTENCIA: v_log_cambios_etapa puede ser MUY lento
        # Consulta cada orden de producción individualmente (~2093 órdenes)
        # Considerar ejecutar por separado o con filtrado
        # results.append(v_log_cambios_etapa.run())  # DESHABILITADO por defecto
        print("\n⚠️  v_log_cambios_etapa DESHABILITADO (ejecutar manualmente si es necesario)")
        
        # =================================================================
        # FIN DE EJECUCIÓN DE CONTROLLERS
        # =================================================================
        
    except KeyboardInterrupt:
        print("\n⚠️  Sincronización interrumpida por el usuario")
        return 130
    
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Imprimir resumen
    print_summary(results, start_time)
    
    # Código de salida
    return 0 if all(r.get('success') for r in results) else 1


def print_summary(results, start_time):
    """Imprime resumen final de la sincronización."""
    end_time = datetime.now()
    total_duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*80)
    print("📊 RESUMEN FINAL")
    print("="*80)
    
    total_fetched = 0
    total_synced = 0
    success_count = 0
    error_count = 0
    
    for result in results:
        controller_name = result.get('controller', 'unknown')
        status_icon = "✅" if result.get('success') else "❌"
        
        print(f"\n{status_icon} {controller_name}")
        print(f"   Extraídos: {result.get('records_fetched', 0):,}")
        print(f"   Sincronizados: {result.get('records_synced', 0):,}")
        print(f"   Duración: {result.get('duration_seconds', 0):.1f}s")
        
        if result.get('error'):
            print(f"   Error: {result['error']}")
        
        total_fetched += result.get('records_fetched', 0)
        total_synced += result.get('records_synced', 0)
        
        if result.get('success'):
            success_count += 1
        else:
            error_count += 1
    
    print("\n" + "="*80)
    print("📈 TOTALES:")
    print(f"   Controllers ejecutados: {len(results)}")
    print(f"   Exitosos: {success_count}")
    print(f"   Con error: {error_count}")
    print(f"   Total extraído: {total_fetched:,} registros")
    print(f"   Total sincronizado: {total_synced:,} registros")
    print(f"   Duración total: {total_duration/60:.1f} minutos")
    if total_duration > 0:
        print(f"   Velocidad: {total_synced/total_duration:.1f} reg/s")
    print("="*80)
    print(f"🏁 Finalizado: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    sys.exit(main())


# =============================================================================
# NOTAS DE USO
# =============================================================================
"""
EJECUCIÓN ESTÁNDAR (sincronización incremental):
    python sync_main.py

EJECUCIÓN MANUAL DE CONTROLLERS ESPECIALES:

1. Log Vidrios Producción con fechas específicas:
    from controllers import log_vidrios_produccion
    log_vidrios_produccion.sync(fecha_desde='2026-01-01', fecha_hasta='2026-01-23')

2. Log Vidrios Producción - carga completa (⚠️ lento):
    from controllers import log_vidrios_produccion
    log_vidrios_produccion.sync(full_sync=True)

3. V Log Cambios Etapa con límite de órdenes:
    from controllers import v_log_cambios_etapa
    # Ejecutar con todas las órdenes (⚠️ MUY lento: ~3 horas)
    v_log_cambios_etapa.run()

VARIABLES DE ENTORNO REQUERIDAS:
    ORACLE_APEX_BASE_URL=https://gsn.maxapex.net/apex/savio
    SUPABASE_URL=https://your-project.supabase.co
    SUPABASE_KEY=your-supabase-key

ORDEN RECOMENDADO DE SINCRONIZACIÓN:
    1. Catálogos (clientes, proyectos, insumos) - datos maestros
    2. Transaccional (cotizaciones, detalle) - dependen de catálogos
    3. Producción (vidrios_produccion) - depende de cotizaciones
    4. Logs (log_vidrios_produccion) - depende de producción

FRECUENCIA RECOMENDADA:
    - Catálogos: cada 1 hora (cambios poco frecuentes)
    - Transaccional: cada 30 minutos (cambios moderados)
    - Producción: cada 30 minutos (cambios frecuentes)
    - Logs: cada 1 hora (alto volumen, usar incremental)

TIMEOUTS Y PERFORMANCE:
    - Total estimado (sin v_log_cambios_etapa): ~2-3 minutos
    - Con v_log_cambios_etapa: +2-3 horas adicionales
    - Usar GitHub Actions con timeout de 10 minutos (suficiente sin v_log_cambios_etapa)
"""
