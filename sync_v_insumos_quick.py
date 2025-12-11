#!/usr/bin/env python3
"""
Script rápido para sincronizar SOLO v_insumos
Sin dependencias complejas
"""

import os
import sys
import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def sync_v_insumos_simple():
    """Sincronización simple y directa de v_insumos"""
    
    print("=" * 80)
    print("🚀 SINCRONIZACIÓN RÁPIDA: v_insumos")
    print("=" * 80)
    
    # Configuración
    base_url = "https://gsn.maxapex.net/apex/savio/v_insumos/"
    username = os.getenv("ORACLE_APEX_USERNAME")
    password = os.getenv("ORACLE_APEX_PASSWORD")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not all([username, password, supabase_url, supabase_key]):
        print("❌ ERROR: Faltan variables de entorno")
        return False
    
    # Importar Supabase
    try:
        from supabase import create_client
    except ImportError:
        print("❌ ERROR: Instala supabase-py: pip install supabase")
        return False
    
    # Cliente Supabase
    supabase = create_client(supabase_url, supabase_key)
    
    # Extraer datos del endpoint
    print(f"\n📥 Extrayendo datos de {base_url}")
    offset = 0
    limit = 100
    total_fetched = 0
    total_inserted = 0
    
    while True:
        try:
            # Hacer request
            params = {"limit": limit, "offset": offset}
            response = requests.get(
                base_url,
                auth=HTTPBasicAuth(username, password),
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Error HTTP {response.status_code}")
                break
            
            data = response.json()
            items = data.get("items", [])
            
            if not items:
                print(f"✅ Extracción completa")
                break
            
            total_fetched += len(items)
            print(f"   Batch: {len(items)} registros (offset: {offset})")
            
            # Transformar e insertar
            for item in items:
                try:
                    # Transformación simple
                    record = {
                        'id': str(item.get('no_insumo')),
                        'no_insumo': item.get('no_insumo'),
                        'clave_estandar': item.get('clave_estandar'),
                        'descripcion': item.get('descripcion'),
                        'nom_largo': item.get('nom_largo'),
                        'tipo_insumo': item.get('tipo_insumo'),
                        'cve_linea': item.get('cve_linea'),
                        'cve_generica': item.get('cve_generica'),
                        'cve_tipo_vidrio': item.get('cve_tipo_vidrio'),
                        'no_espesor': item.get('no_espesor'),
                        'no_medida': item.get('no_medida'),
                        'no_acabado': item.get('no_acabado'),
                        'no_longitud': item.get('no_longitud'),
                        'cve_unidad': item.get('cve_unidad'),
                        'precio_mxn': item.get('precio_mxn'),
                        'precio_usd': item.get('precio_usd'),
                        'precio_eur': item.get('precio_eur'),
                        'costo_promedio': item.get('costo_promedio'),
                        'no_insumo_gsns': item.get('no_insumo_gsns'),
                        'espesor': item.get('espesor'),
                        'vigente': item.get('vigente'),
                        'id_skyplanner': item.get('id_skyplanner'),
                        'tiempo_pre_proceso': item.get('tiempo_pre_proceso'),
                        'tiempo_proceso': item.get('tiempo_proceso'),
                        'tiempo_post_proceso': item.get('tiempo_post_proceso')
                    }
                    
                    # UPSERT en Supabase
                    result = supabase.table('v_insumos').upsert(record).execute()
                    total_inserted += 1
                    
                except Exception as e:
                    print(f"   ⚠️  Error en registro {item.get('no_insumo')}: {e}")
                    continue
            
            print(f"   💾 Insertados: {total_inserted}")
            
            # Siguiente batch
            offset += limit
            
        except Exception as e:
            print(f"❌ Error en batch: {e}")
            break
    
    # Resumen
    print("\n" + "=" * 80)
    print("✅ SINCRONIZACIÓN COMPLETADA")
    print("=" * 80)
    print(f"📥 Total extraído: {total_fetched:,} registros")
    print(f"💾 Total insertado: {total_inserted:,} registros")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = sync_v_insumos_simple()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Sincronización interrumpida")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
