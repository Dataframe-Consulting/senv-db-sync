#!/usr/bin/env python3
"""
Sincronización COMPLETA del endpoint v_insumos
Usa streaming para insertar mientras extrae (previene pérdida de datos).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
from src.clients import OracleApexClient, SupabaseClient
from src.services.streaming_sync_service import StreamingSyncService
from src.config.settings import OracleApexConfig, SupabaseConfig, SyncConfig
from transforms_all_savio import transform_v_insumos

load_dotenv()

def sync_v_insumos():
    """Sincronización completa del endpoint v_insumos."""
    
    print("=" * 80)
    print("🚀 SINCRONIZACIÓN: v_insumos → v_insumos")
    print("=" * 80)
    print()
    
    # Configuración
    oracle_config = OracleApexConfig(
        base_url="https://gsn.maxapex.net/apex/savio",
        endpoint="v_insumos",
        username=os.getenv("ORACLE_APEX_USERNAME"),
        password=os.getenv("ORACLE_APEX_PASSWORD"),
        timeout=60,
        max_retries=3,
        retry_delay=2
    )
    
    supabase_config = SupabaseConfig(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_KEY"),
        table_name="v_insumos"
    )
    
    sync_config = SyncConfig(batch_size=100)
    
    class SimpleConfig:
        def __init__(self, oracle, supabase, sync):
            self.oracle = oracle
            self.supabase = supabase
            self.sync = sync
    
    simple_config = SimpleConfig(oracle_config, supabase_config, sync_config)
    
    # Clientes
    oracle_client = OracleApexClient(oracle_config, sync_config)
    supabase_client = SupabaseClient(supabase_config)
    
    # Servicio de sincronización con streaming
    sync_service = StreamingSyncService(oracle_client, supabase_client, simple_config)
    
    print("📊 Endpoint: https://gsn.maxapex.net/apex/savio/v_insumos/")
    print("💾 Tabla Supabase: v_insumos")
    print("🔄 Modo: Streaming (insertar mientras extrae)")
    print("📦 Batch: 100 registros por lote")
    print()
    print("-" * 80)
    print()
    
    try:
        # Ejecutar sync
        result = sync_service.sync_data(
            id_field='id',
            transform_fn=transform_v_insumos
        )
        
        # Calcular duración
        duration = 0
        if result.started_at and result.completed_at:
            duration = (result.completed_at - result.started_at).total_seconds()
        
        print()
        print("=" * 80)
        print("✅ SINCRONIZACIÓN COMPLETADA")
        print("=" * 80)
        print(f"📥 Total extraído: {result.total_fetched:,} registros")
        print(f"💾 Total insertado: {result.total_inserted:,} registros")
        print(f"⏱️  Tiempo total: {duration:.2f} segundos")
        
        if result.total_inserted > 0 and duration > 0:
            rate = result.total_inserted / duration
            print(f"⚡ Velocidad: {rate:.1f} registros/segundo")
        
        if result.total_errors > 0:
            print(f"\n⚠️  Errores encontrados: {result.total_errors}")
            for error in result.errors[:5]:  # Mostrar primeros 5 errores
                print(f"   - {error}")
        
        print()
        
    except KeyboardInterrupt:
        print()
        print("=" * 80)
        print("⚠️  SINCRONIZACIÓN INTERRUMPIDA")
        print("=" * 80)
        print("✅ Los registros insertados hasta ahora están guardados en Supabase")
        print("💡 Puedes reanudar ejecutando este script nuevamente")
        print()
        sys.exit(0)
    
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR EN SINCRONIZACIÓN")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    sync_v_insumos()
