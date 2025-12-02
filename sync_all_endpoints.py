#!/usr/bin/env python3
"""
Script principal para sincronizar todos los endpoints del ERP SAVIO a Supabase.
Diseñado para ejecutarse en GitHub Actions cada hora.
Incluye UPSERT automático para evitar duplicados.
"""

import sys
import os
from datetime import datetime
from typing import Dict, Any, Tuple
import time

# Añadir el directorio actual al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
from src.clients import OracleApexClient, SupabaseClient
from src.config.settings import OracleApexConfig, SupabaseConfig, SyncConfig
from transforms_all_savio import TRANSFORMATIONS, TABLES

# Cargar variables de entorno
load_dotenv()


class EndpointSyncManager:
    """Gestor de sincronización para múltiples endpoints."""
    
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        
    def sync_endpoint(
        self,
        endpoint_name: str,
        table_name: str,
        transform_fn: callable,
        batch_size: int = 100
    ) -> Tuple[int, int, str]:
        """
        Sincroniza un endpoint específico.
        
        Args:
            endpoint_name: Nombre del endpoint en Oracle APEX
            table_name: Nombre de la tabla en Supabase
            transform_fn: Función de transformación
            batch_size: Tamaño del lote
            
        Returns:
            Tupla con (total_fetched, total_inserted, status)
        """
        print(f"\n{'='*80}")
        print(f"🔄 Sincronizando: {endpoint_name}")
        print(f"📊 Tabla destino: {table_name}")
        print(f"{'='*80}")
        
        try:
            # Configurar clientes
            oracle_config = OracleApexConfig(
                base_url="https://gsn.maxapex.net/ords/savio",
                endpoint=endpoint_name,
                username=os.getenv("ORACLE_APEX_USERNAME"),
                password=os.getenv("ORACLE_APEX_PASSWORD"),
                timeout=int(os.getenv("REQUEST_TIMEOUT", 60)),
                max_retries=int(os.getenv("MAX_RETRIES", 3)),
                retry_delay=int(os.getenv("RETRY_DELAY", 2))
            )
            
            supabase_config = SupabaseConfig(
                url=os.getenv("SUPABASE_URL"),
                key=os.getenv("SUPABASE_KEY"),
                table_name=table_name
            )
            
            sync_config = SyncConfig(batch_size=batch_size)
            
            oracle_client = OracleApexClient(oracle_config, sync_config)
            supabase_client = SupabaseClient(supabase_config)
            
            # Variables de progreso
            offset = 0
            total_fetched = 0
            total_inserted = 0
            report_interval = 1000
            last_report = 0
            
            endpoint_start = datetime.now()
            
            # Sincronización con streaming
            while True:
                # Extraer batch
                records, success = oracle_client._fetch_batch(offset)
                
                if not success:
                    print(f"⚠️  Error al extraer batch en offset {offset}")
                    break
                
                if not records:
                    print(f"✅ Extracción completa")
                    break
                
                batch_size = len(records)
                total_fetched += batch_size
                
                # Transformar registros
                try:
                    transformed = [transform_fn(r) for r in records]
                except Exception as e:
                    print(f"❌ Error al transformar batch: {e}")
                    offset += sync_config.batch_size
                    continue
                
                # Insertar con UPSERT (evita duplicados)
                try:
                    inserted = supabase_client.batch_upsert(
                        transformed,
                        batch_size=100,
                        conflict_column='id'
                    )
                    total_inserted += inserted
                except Exception as e:
                    print(f"❌ Error al insertar batch: {e}")
                
                # Reportar progreso
                if total_inserted >= last_report + report_interval:
                    elapsed = (datetime.now() - endpoint_start).total_seconds()
                    rate = total_inserted / elapsed if elapsed > 0 else 0
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                          f"📊 {total_inserted:,} registros | "
                          f"⚡ {rate:.1f} reg/s")
                    last_report = total_inserted
                
                # Avanzar offset
                offset += sync_config.batch_size
                time.sleep(0.05)  # Pequeña pausa para no sobrecargar
            
            # Calcular estadísticas
            elapsed = (datetime.now() - endpoint_start).total_seconds()
            
            print(f"\n✅ COMPLETADO: {endpoint_name}")
            print(f"   📥 Extraídos: {total_fetched:,} registros")
            print(f"   💾 Insertados/Actualizados: {total_inserted:,} registros")
            print(f"   ⏱️  Tiempo: {elapsed/60:.1f} minutos")
            print(f"   ⚡ Velocidad: {total_inserted/elapsed:.1f} reg/s")
            
            return total_fetched, total_inserted, "SUCCESS"
            
        except Exception as e:
            print(f"\n❌ ERROR en {endpoint_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            return 0, 0, f"ERROR: {str(e)}"
    
    def sync_all(self):
        """Sincroniza todos los endpoints configurados."""
        print("\n" + "="*80)
        print("🚀 SINCRONIZACIÓN AUTOMÁTICA ERP → SUPABASE")
        print("="*80)
        print(f"⏰ Iniciado: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Definir endpoints a sincronizar (en orden de prioridad)
        endpoints = [
            {
                'name': 'v_log_cambios_etapa',
                'table': TABLES['v_log_cambios_etapa'],
                'transform': TRANSFORMATIONS['v_log_cambios_etapa'],
                'batch_size': 100
            },
            {
                'name': 'detalle_cotizacion',
                'table': TABLES['detalle_cotizacion'],
                'transform': TRANSFORMATIONS['detalle_cotizacion'],
                'batch_size': 100
            },
            {
                'name': 'vidrios_produccion',
                'table': TABLES['vidrios_produccion'],
                'transform': TRANSFORMATIONS['vidrios_produccion'],
                'batch_size': 100
            },
            {
                'name': 'log_vidrios_produccion',
                'table': TABLES['log_vidrios_produccion'],
                'transform': TRANSFORMATIONS['log_vidrios_produccion'],
                'batch_size': 100
            }
        ]
        
        # Sincronizar cada endpoint
        for endpoint_config in endpoints:
            fetched, inserted, status = self.sync_endpoint(
                endpoint_name=endpoint_config['name'],
                table_name=endpoint_config['table'],
                transform_fn=endpoint_config['transform'],
                batch_size=endpoint_config['batch_size']
            )
            
            self.results[endpoint_config['name']] = {
                'fetched': fetched,
                'inserted': inserted,
                'status': status,
                'table': endpoint_config['table']
            }
        
        # Resumen final
        self.print_summary()
        
        # Determinar código de salida
        return self.get_exit_code()
    
    def print_summary(self):
        """Imprime un resumen final de la sincronización."""
        end_time = datetime.now()
        total_time = (end_time - self.start_time).total_seconds()
        
        print("\n" + "="*80)
        print("📊 RESUMEN DE SINCRONIZACIÓN")
        print("="*80)
        
        total_fetched = 0
        total_inserted = 0
        success_count = 0
        error_count = 0
        
        for endpoint, result in self.results.items():
            status_icon = "✅" if result['status'] == "SUCCESS" else "❌"
            print(f"\n{status_icon} {endpoint}")
            print(f"   Tabla: {result['table']}")
            print(f"   Extraídos: {result['fetched']:,}")
            print(f"   Insertados: {result['inserted']:,}")
            print(f"   Estado: {result['status']}")
            
            total_fetched += result['fetched']
            total_inserted += result['inserted']
            
            if result['status'] == "SUCCESS":
                success_count += 1
            else:
                error_count += 1
        
        print("\n" + "="*80)
        print(f"📈 TOTALES:")
        print(f"   Total extraído: {total_fetched:,} registros")
        print(f"   Total insertado: {total_inserted:,} registros")
        print(f"   Endpoints exitosos: {success_count}/{len(self.results)}")
        print(f"   Endpoints con error: {error_count}/{len(self.results)}")
        print(f"   Tiempo total: {total_time/60:.1f} minutos")
        print(f"   Velocidad promedio: {total_inserted/total_time:.1f} reg/s")
        print("="*80)
        print(f"🏁 Finalizado: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
    
    def get_exit_code(self) -> int:
        """Retorna código de salida apropiado para CI/CD."""
        for result in self.results.values():
            if result['status'] != "SUCCESS":
                return 1  # Error
        return 0  # Éxito


def main():
    """Función principal."""
    try:
        # Verificar variables de entorno requeridas
        required_vars = [
            'ORACLE_APEX_USERNAME',
            'ORACLE_APEX_PASSWORD',
            'SUPABASE_URL',
            'SUPABASE_KEY'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"❌ ERROR: Faltan variables de entorno: {', '.join(missing_vars)}")
            print("💡 Configura los secretos en GitHub Actions:")
            print("   Settings → Secrets and variables → Actions → New repository secret")
            return 1
        
        # Ejecutar sincronización
        manager = EndpointSyncManager()
        exit_code = manager.sync_all()
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\n⚠️  Sincronización interrumpida por el usuario")
        return 130
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
