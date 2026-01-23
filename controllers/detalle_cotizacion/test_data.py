"""
Script de prueba para el controller de Detalle Cotización.
Extrae y transforma datos sin sincronizar a Supabase.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(root_dir))

from controllers.detalle_cotizacion.components import get_data
from controllers.detalle_cotizacion.components import transform_data
from controllers.detalle_cotizacion.components import synchronize


def test_data_extraction(verbose: bool = True, show_sample: int = 3):
    """
    Prueba la extracción y transformación de datos sin sincronizar.
    
    Args:
        verbose: Si mostrar logs de progreso
        show_sample: Número de registros de ejemplo a mostrar
        
    Returns:
        Dict con los datos transformados y estadísticas
    """
    start_time = datetime.now()
    
    result = {
        'controller': 'detalle_cotizacion',
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
            print("🧪 TEST DE DATOS: Detalle Cotización (SIN SINCRONIZAR)")
            print("="*70)
        
        # PASO 1: Información previa
        if verbose:
            print("\n📊 Paso 1/3: Información actual de Supabase...")
        synchronize.get_last_sync_info(verbose=verbose)
        
        # PASO 2: Extraer datos
        if verbose:
            print("\n📥 Paso 2/3: Extrayendo datos del endpoint...")
        
        records, success = get_data.fetch_all(verbose=verbose)
        
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
            print(f"\n🔄 Paso 3/3: Transformando {len(records):,} registros...")
        
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
    # Ejecutar test
    result = test_data_extraction(verbose=True, show_sample=3)
    
    # Guardar resultado completo en archivo JSON
    if result['success']:
        output_file = f"test_detalle_cotizacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n💾 Resultado completo guardado en: {output_file}")
