#!/usr/bin/env python3
"""
Sincronización COMPLETA del endpoint v_log_cambios_etapa con logs visibles.
Muestra progreso en tiempo real cada 500 registros.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
from src.clients import OracleApexClient, SupabaseClient
from src.config.settings import OracleApexConfig, SupabaseConfig, SyncConfig
from transforms_all_savio import transform_log_cambios_etapa
import time
from datetime import datetime

load_dotenv()

def sync_with_progress():
    """Sincronización con progreso visible."""
    
    print("=" * 80)
    print("🚀 SINCRONIZACIÓN CON PROGRESO VISIBLE")
    print("=" * 80)
    print(f"📊 Endpoint: v_log_cambios_etapa")
    print(f"💾 Tabla: log_cambios_etapa")
    print(f"🎯 Meta: 151,990 registros")
    print("=" * 80)
    print()
    
    # Configuración
    oracle_config = OracleApexConfig(
        base_url="https://gsn.maxapex.net/ords/savio",
        endpoint="v_log_cambios_etapa",
        username=os.getenv("ORACLE_APEX_USERNAME"),
        password=os.getenv("ORACLE_APEX_PASSWORD"),
        timeout=60,
        max_retries=3,
        retry_delay=2
    )
    
    supabase_config = SupabaseConfig(
        url=os.getenv("SUPABASE_URL"),
        key=os.getenv("SUPABASE_KEY"),
        table_name="log_cambios_etapa"
    )
    
    sync_config = SyncConfig(batch_size=100)
    
    oracle_client = OracleApexClient(oracle_config, sync_config)
    supabase_client = SupabaseClient(supabase_config)
    
    # Variables de progreso
    offset = 0
    total_fetched = 0
    total_inserted = 0
    start_time = datetime.now()
    last_report = 0
    report_interval = 500  # Reportar cada 500 registros
    
    try:
        while True:
            # Extraer batch
            records, success = oracle_client._fetch_batch(offset)
            
            if not success:
                print(f"❌ Error al extraer batch en offset {offset}")
                break
            
            if not records:
                print(f"\n✅ No hay más registros. Extracción completa.")
                break
            
            batch_size = len(records)
            total_fetched += batch_size
            
            # Transformar
            transformed = [transform_log_cambios_etapa(r) for r in records]
            
            # Insertar
            try:
                inserted = supabase_client.batch_upsert(
                    transformed,
                    batch_size=100,
                    conflict_column='id'
                )
                total_inserted += inserted
            except Exception as e:
                print(f"\n❌ Error al insertar batch: {e}")
                # Continuar con el siguiente batch
            
            # Reportar progreso cada X registros
            if total_inserted >= last_report + report_interval:
                elapsed = (datetime.now() - start_time).total_seconds()
                rate = total_inserted / elapsed if elapsed > 0 else 0
                progress = (total_inserted / 151990) * 100
                remaining = 151990 - total_inserted
                eta = remaining / rate if rate > 0 else 0
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                      f"📊 {total_inserted:,} / 151,990 ({progress:.1f}%) | "
                      f"⚡ {rate:.1f} reg/s | "
                      f"⏳ ETA: {eta/60:.1f} min")
                
                last_report = total_inserted
            
            # Avanzar offset
            offset += sync_config.batch_size
            time.sleep(0.1)  # Pausa pequeña
        
        # Resumen final
        elapsed = (datetime.now() - start_time).total_seconds()
        print()
        print("=" * 80)
        print("✅ SINCRONIZACIÓN COMPLETADA")
        print("=" * 80)
        print(f"📥 Total extraído: {total_fetched:,} registros")
        print(f"💾 Total insertado: {total_inserted:,} registros")
        print(f"⏱️  Tiempo total: {elapsed/60:.1f} minutos")
        print(f"⚡ Velocidad promedio: {total_inserted/elapsed:.1f} reg/s")
        print("=" * 80)
        
    except KeyboardInterrupt:
        elapsed = (datetime.now() - start_time).total_seconds()
        print()
        print("=" * 80)
        print("⚠️  SINCRONIZACIÓN INTERRUMPIDA")
        print("=" * 80)
        print(f"📊 Progreso: {total_inserted:,} / 151,990 ({total_inserted/151990*100:.1f}%)")
        print(f"⏱️  Tiempo transcurrido: {elapsed/60:.1f} minutos")
        print(f"✅ Los {total_inserted:,} registros insertados están en Supabase")
        print("💡 Ejecuta este script nuevamente para continuar")
        print("=" * 80)
    
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        print(f"📊 Insertados hasta ahora: {total_inserted:,}")
        print("=" * 80)

if __name__ == "__main__":
    sync_with_progress()
