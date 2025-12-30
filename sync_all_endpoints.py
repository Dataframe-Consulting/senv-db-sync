#!/usr/bin/env python3
"""
Script principal para sincronizar todos los endpoints del ERP SAVIO a Supabase.
Diseñado para ejecutarse en GitHub Actions cada hora.
Incluye UPSERT automático para evitar duplicados.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Tuple, List
import time

# Añadir el directorio actual al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from dotenv import load_dotenv
from src.clients import OracleApexClient, SupabaseClient
from src.config.settings import OracleApexConfig, SupabaseConfig, SyncConfig
from transforms_all_savio import TRANSFORMATIONS, TABLES

# Cargar variables de entorno
load_dotenv()


def load_endpoints_config() -> List[Dict[str, str]]:
    """Carga la configuración de endpoints desde el archivo JSON."""
    config_path = os.path.join(
        os.path.dirname(__file__),
        'src',
        'config',
        'endpoints_tables.json'
    )
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


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
            oracle_config = OracleApexConfig.from_env(endpoint_name)
            supabase_config = SupabaseConfig.from_env(table_name)
            sync_config = SyncConfig.from_env()
            
            oracle_client = OracleApexClient(oracle_config, sync_config)
            supabase_client = SupabaseClient(supabase_config)

            # Obtener última fecha de sincronización para sync incremental
            last_sync_date = supabase_client.get_max_date('fec_modif')
            if last_sync_date:
                print(f"📅 Última sincronización: {last_sync_date}")
                print(f"🔄 Modo: Incremental (solo cambios desde {last_sync_date})")
            else:
                print(f"🆕 Primera sincronización: Descargando todos los registros")

            # Variables de progreso
            offset = 0
            total_fetched = 0
            total_inserted = 0
            report_interval = 5000
            last_report = 0

            endpoint_start = datetime.now()

            # Sincronización con streaming
            while True:
                # Extraer batch con filtrado incremental
                records, success = oracle_client._fetch_batch(offset, last_sync_date)
                
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
                    
                    # Deduplicar por ID antes de insertar (mantener el último)
                    unique_records = {}
                    for record in transformed:
                        unique_records[record['id']] = record
                    transformed = list(unique_records.values())
                    
                    if len(transformed) < len(records):
                        print(f"⚠️  Duplicados removidos: {len(records) - len(transformed)}")
                        
                except Exception as e:
                    print(f"❌ Error al transformar batch: {e}")
                    offset += sync_config.batch_size
                    continue
                
                # Insertar con UPSERT (evita duplicados) con retry y backoff
                max_retries = 3
                retry_count = 0
                inserted = 0

                while retry_count < max_retries:
                    try:
                        inserted = supabase_client.batch_upsert(
                            transformed,
                            batch_size=1000,  # Optimizado: restaurado a 1000 con mejor manejo de errores
                            conflict_column='id'
                        )
                        total_inserted += inserted
                        break  # Éxito, salir del loop de retry
                    except Exception as e:
                        retry_count += 1
                        if retry_count >= max_retries:
                            print(f"❌ Error al insertar batch después de {max_retries} intentos: {e}")
                            # Registrar error pero continuar (no perder todo el sync)
                        else:
                            wait_time = 2 ** retry_count  # Exponential backoff: 2s, 4s, 8s
                            print(f"⚠️  Error al insertar batch (intento {retry_count}/{max_retries}): {e}")
                            print(f"⏳ Reintentando en {wait_time} segundos...")
                            time.sleep(wait_time)
                
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

                # Rate limiting: pausa de 500ms entre batches para no saturar Supabase
                time.sleep(0.5)
            
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
        
        # Cargar configuración de endpoints desde JSON
        try:
            endpoints_config = load_endpoints_config()
            print(f"📋 Endpoints cargados: {len(endpoints_config)}")
        except Exception as e:
            print(f"❌ Error al cargar configuración de endpoints: {e}")
            return 1
        
        # Construir lista de endpoints a sincronizar
        endpoints = []
        for config in endpoints_config:
            endpoint_name = config['endpoint']
            table_name = config['table']
            
            # Verificar que existan las transformaciones
            if endpoint_name not in TRANSFORMATIONS:
                print(f"⚠️  Warning: No hay transformación para {endpoint_name}, omitiendo...")
                continue
            
            if endpoint_name not in TABLES:
                print(f"⚠️  Warning: No hay tabla definida para {endpoint_name}, omitiendo...")
                continue
            
            endpoints.append({
                'name': endpoint_name,
                'table': table_name,
                'transform': TRANSFORMATIONS[endpoint_name],
                'batch_size': 100
            })
        
        print(f"✅ Endpoints válidos a sincronizar: {len(endpoints)}\n")
        
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
