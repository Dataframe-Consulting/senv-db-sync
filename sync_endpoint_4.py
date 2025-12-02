#!/usr/bin/env python3
"""
Sincronización del endpoint 4: log_vidrios_produccion
Total estimado: 272,916 registros
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
from src.clients import OracleApexClient, SupabaseClient
from src.config.settings import OracleApexConfig, SupabaseConfig, SyncConfig
from transforms_all_savio import transform_log_vidrios_produccion
import time
from datetime import datetime

load_dotenv()

def main():
    """Sincroniza el endpoint log_vidrios_produccion con progreso visible"""
    
    print("=" * 80)
    print("🚀 SINCRONIZACIÓN CON PROGRESO VISIBLE")
    print("=" * 80)
    print("📊 Endpoint: log_vidrios_produccion")
    print("💾 Tabla: log_vidrios_produccion")
    print("🎯 Meta: 272,916 registros")
    print("=" * 80)
    print()
    
    # Configuración
    oracle_config = OracleApexConfig(
        base_url=os.getenv('ORACLE_APEX_BASE_URL'),
        username=os.getenv('ORACLE_APEX_USERNAME'),
        password=os.getenv('ORACLE_APEX_PASSWORD'),
        endpoint='log_vidrios_produccion'
    )
    
    supabase_config = SupabaseConfig(
        url=os.getenv('SUPABASE_URL'),
        key=os.getenv('SUPABASE_KEY'),
        table_name='log_vidrios_produccion'
    )
    
    sync_config = SyncConfig(
        batch_size=100,
        max_retries=3,
        retry_delay=5
    )
    
    # Clientes
    oracle_client = OracleApexClient(oracle_config, sync_config)
    supabase_client = SupabaseClient(supabase_config)
    
    # Variables de progreso
    start_time = time.time()
    last_report_count = 0
    report_interval = 1000  # Reportar cada 1000 registros (más grande)
    
    try:
        # Sync con progreso
        total = 0
        offset = 0
        
        while True:
            # Extraer batch
            records, success = oracle_client._fetch_batch(offset)
            
            if not success:
                print(f"❌ Error al extraer batch en offset {offset}")
                break
            
            if not records:
                print()
                print("✅ No hay más registros. Extracción completa.")
                break
            
            # Transformar
            transformed = [transform_log_vidrios_produccion(r) for r in records]
            
            # Insertar en Supabase
            inserted = supabase_client.batch_upsert(
                transformed,
                batch_size=100,
                conflict_column='id'
            )
            
            # Actualizar contador
            total += inserted
            
            # Reportar progreso cada report_interval registros
            if total - last_report_count >= report_interval or len(records) < sync_config.batch_size:
                elapsed = time.time() - start_time
                rate = total / elapsed if elapsed > 0 else 0
                remaining = 272916 - total
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60
                
                timestamp = datetime.now().strftime("%H:%M:%S")
                percentage = (total / 272916) * 100
                
                print(f"[{timestamp}] 📊 {total:,} / 272,916 ({percentage:.1f}%) | "
                      f"⚡ {rate:.1f} reg/s | ⏳ ETA: {eta_minutes:.1f} min")
                
                last_report_count = total
            
            # Avanzar offset
            offset += sync_config.batch_size
        
        # Resumen final
        elapsed = time.time() - start_time
        elapsed_minutes = elapsed / 60
        avg_rate = total / elapsed if elapsed > 0 else 0
        
        print()
        print("=" * 80)
        print("✅ SINCRONIZACIÓN COMPLETADA")
        print("=" * 80)
        print(f"📥 Total extraído: {total:,} registros")
        print(f"💾 Total insertado: {total:,} registros")
        print(f"⏱️  Tiempo total: {elapsed_minutes:.1f} minutos")
        print(f"⚡ Velocidad promedio: {avg_rate:.1f} reg/s")
        print("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print()
        print("⚠️  SINCRONIZACIÓN INTERRUMPIDA POR EL USUARIO")
        print(f"📊 Progreso alcanzado: {total:,} / 272,916 registros")
        return 1
        
    except Exception as e:
        print()
        print(f"❌ ERROR: {e}")
        print(f"📊 Progreso alcanzado: {total:,} / 272,916 registros")
        return 1

if __name__ == "__main__":
    sys.exit(main())
