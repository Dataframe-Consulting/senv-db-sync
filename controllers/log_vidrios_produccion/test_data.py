"""
Script de prueba para el controller de Log Vidrios Producción.
Extrae y transforma datos sin sincronizar a Supabase.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

# Cargar variables de entorno
from dotenv import load_dotenv
load_dotenv()

from controllers.log_vidrios_produccion.components import get_data
from controllers.log_vidrios_produccion.components import transform_data
from controllers.log_vidrios_produccion.components import synchronize


def test_data_extraction(
    fecha_desde: str = None,
    fecha_hasta: str = None,
    dias_historico: int = 30,
    full_sync: bool = False,
    verbose: bool = True,
    show_sample: int = 3
):
    """
    Prueba la extracción y transformación de datos sin sincronizar.
    
    Estrategia:
    - Si full_sync=True: sin filtro (todos los registros)
    - Si fecha_desde: usa fecha manual
    - Si no: usa fecha incremental desde Supabase
    
    Args:
        fecha_desde: Fecha desde (formato: YYYY-MM-DD)
        fecha_hasta: Fecha hasta (formato: YYYY-MM-DD)
        dias_historico: Días hacia atrás si full_sync o primera sync (default: 30)
        full_sync: Si True, descarga todos los registros sin filtro
        verbose: Si mostrar logs de progreso
        show_sample: Número de registros de ejemplo a mostrar
        
    Returns:
        Dict con los datos transformados y estadísticas
    """
    start_time = datetime.now()
    
    result = {
        'controller': 'log_vidrios_produccion',
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'success': False,
        'records_fetched': 0,
        'records_transformed': 0,
        'records_unique': 0,
        'duration_seconds': 0.0,
        'sample_data': [],
        'error': None
    }
    
    try:
        if verbose:
            print("\n" + "="*70)
            print("🧪 TEST DE DATOS: Log Vidrios Producción (SIN SINCRONIZAR)")
            print("="*70)
        
        # PASO 1: Información previa
        if verbose:
            print("\n📊 Paso 1/4: Información actual de Supabase...")
        sync_info = synchronize.get_last_sync_info(verbose=verbose)
        
        # PASO 2: Determinar rango de fechas
        if verbose:
            print("\n📅 Paso 2/4: Determinando rango de fechas...")
        
        # Determinar fecha_desde
        fecha_desde_calc = fecha_desde
        if fecha_desde_calc:
            # Usuario especificó fecha manualmente
            if verbose:
                print(f"   📅 Usando fecha manual: {fecha_desde_calc}")
        elif full_sync:
            # Full sync: sin filtro
            fecha_desde_calc = None
            if verbose:
                print(f"   🔄 Full sync: sin filtro (todos los registros)")
        else:
            # Sincronización incremental: desde última fecha en Supabase
            last_modified = sync_info.get('last_modified')
            if last_modified:
                # Convertir a formato YYYY-MM-DD
                if 'T' in last_modified:
                    fecha_desde_calc = last_modified.split('T')[0]
                elif ' ' in last_modified:
                    fecha_desde_calc = last_modified.split(' ')[0]
                else:
                    fecha_desde_calc = last_modified
                
                if verbose:
                    print(f"   ⚡ Sincronización incremental desde última modificación: {fecha_desde_calc}")
            else:
                # Primera sincronización: TODOS los registros históricos
                fecha_desde_calc = None
                fecha_hasta_calc = None
                if verbose:
                    print(f"   🆕 Primera sincronización: TODOS los registros históricos (sin filtro)")
                    print(f"   ⚠️  Esto puede tomar varios minutos...")
        
        # Determinar fecha_hasta
        fecha_hasta_calc = fecha_hasta
        if not fecha_hasta_calc and not full_sync:
            fecha_hasta_calc = datetime.now().strftime('%Y-%m-%d')
        
        if verbose and fecha_desde_calc:
            print(f"   📅 Rango final: {fecha_desde_calc} → {fecha_hasta_calc or 'hoy'}")
        
        # PASO 3: Extraer datos
        if verbose:
            print("\n📥 Paso 3/4: Extrayendo datos del endpoint...")
        
        records, success = get_data.fetch_all(
            fecha_desde=fecha_desde_calc,
            fecha_hasta=fecha_hasta_calc,
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
            print(f"\n🔄 Paso 4/4: Transformando {len(records):,} registros...")
        
        transformed = transform_data.transform_all(records)
        
        if not transformed:
            result['error'] = "Error en transformación"
            return result
        
        result['records_transformed'] = len(transformed)
        
        # Deduplicar
        unique_records = transform_data.deduplicate_by_id(transformed)
        result['records_unique'] = len(unique_records)
        
        # Guardar muestra de datos
        result['sample_data'] = unique_records[:show_sample]
        result['success'] = True
        
        duration = (datetime.now() - start_time).total_seconds()
        result['duration_seconds'] = duration
        
        if verbose:
            print("\n" + "="*70)
            print("✅ DATOS EXTRAÍDOS Y TRANSFORMADOS (NO SINCRONIZADOS)")
            print(f"   📥 Extraídos: {result['records_fetched']:,}")
            print(f"   🔄 Transformados: {result['records_transformed']:,}")
            print(f"   ✨ Únicos: {result['records_unique']:,}")
            print(f"   ⏱️  Duración: {duration:.1f}s")
            print("="*70)
            
            if result['sample_data']:
                print(f"\n📝 Muestra de {min(show_sample, len(unique_records))} registro(s):")
                print("-"*70)
                for i, record in enumerate(result['sample_data'], 1):
                    print(f"\nRegistro {i}:")
                    print(json.dumps(record, indent=2, ensure_ascii=False, default=str))
                print("-"*70)
        
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


if __name__ == "__main__":
    import sys
    
    # Parsear argumentos de línea de comandos
    fecha_desde = None
    fecha_hasta = None
    dias_historico = 30
    full_sync = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help']:
            print("\n🧪 Test de Log Vidrios Producción (SIN SINCRONIZAR)")
            print("="*70)
            print("\nUso:")
            print("  python test_data.py                      # Incremental (desde última sync)")
            print("  python test_data.py --full              # Full sync (todos los registros)")
            print("  python test_data.py 2026-01-01          # Desde fecha específica hasta hoy")
            print("  python test_data.py 2026-01-01 2026-01-23  # Rango específico")
            print("\nModos:")
            print("  INCREMENTAL (default): Consulta Supabase y sincroniza desde última fecha")
            print("  FULL (--full): Sin filtro, todos los registros históricos")
            print("  MANUAL (con fechas): Usa las fechas que especifiques")
            print("\nEjemplos:")
            print("  python test_data.py                      # Incremental desde última sync")
            print("  python test_data.py --full              # Todos los registros (⚠️ lento)")
            print("  python test_data.py 2026-01-01          # Desde 1 enero hasta hoy")
            print("  python test_data.py 2026-01-01 2026-01-15  # Del 1 al 15 enero")
            print("="*70)
            sys.exit(0)
        
        # Verificar si es full sync
        if sys.argv[1] == '--full':
            full_sync = True
        else:
            # Primer argumento: fecha_desde
            fecha_desde = sys.argv[1]
            
            # Segundo argumento: fecha_hasta (opcional)
            if len(sys.argv) > 2:
                fecha_hasta = sys.argv[2]
    
    # Ejecutar test
    result = test_data_extraction(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        dias_historico=dias_historico,
        full_sync=full_sync,
        verbose=True,
        show_sample=3
    )
    
    # Guardar resultado completo en archivo JSON
    if result['success']:
        if full_sync:
            fecha_str = "full"
        elif fecha_desde:
            fecha_str = f"{fecha_desde}_{fecha_hasta or 'hoy'}"
        else:
            fecha_str = "incremental"
        
        output_file = f"test_log_vidrios_produccion_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{fecha_str}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Resultado completo guardado en: {output_file}")
