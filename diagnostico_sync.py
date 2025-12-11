#!/usr/bin/env python3
"""
Script de diagnóstico para verificar la sincronización de los 4 nuevos endpoints.
Compara el total de registros en Oracle APEX vs Supabase.
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import requests
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def count_apex_records(endpoint_url, username, password):
    """Cuenta los registros totales en un endpoint de Oracle APEX."""
    try:
        total_count = 0
        offset = 0
        limit = 1000
        
        while True:
            response = requests.get(
                endpoint_url,
                auth=HTTPBasicAuth(username, password),
                params={'limit': limit, 'offset': offset},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                
                if not items:
                    break
                
                total_count += len(items)
                has_more = data.get('hasMore', False)
                
                if not has_more:
                    break
                    
                offset += limit
            else:
                return None, f"HTTP {response.status_code}"
                
        return total_count, None
        
    except Exception as e:
        return None, str(e)


def count_supabase_records(supabase_client, table_name):
    """Cuenta los registros en una tabla de Supabase."""
    try:
        response = supabase_client.table(table_name).select('id', count='exact').limit(1).execute()
        return response.count, None
    except Exception as e:
        return None, str(e)


def main():
    print("=" * 100)
    print("🔍 DIAGNÓSTICO DE SINCRONIZACIÓN - COMPARACIÓN APEX vs SUPABASE")
    print("=" * 100)
    print()
    
    # Configuración
    apex_username = os.getenv('ORACLE_APEX_USERNAME')
    apex_password = os.getenv('ORACLE_APEX_PASSWORD')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not all([apex_username, apex_password, supabase_url, supabase_key]):
        print("❌ ERROR: Faltan variables de entorno")
        return 1
    
    # Crear cliente Supabase
    supabase = create_client(supabase_url, supabase_key)
    
    # Endpoints a verificar (los 4 nuevos)
    endpoints = [
        {
            'name': 'cotizaciones',
            'apex_url': 'https://gsn.maxapex.net/apex/savio/cotizaciones/',
            'supabase_table': 'cotizaciones'
        },
        {
            'name': 'clientes',
            'apex_url': 'https://gsn.maxapex.net/apex/savio/clientes/',
            'supabase_table': 'clientes'
        },
        {
            'name': 'proyectos_cliente',
            'apex_url': 'https://gsn.maxapex.net/apex/savio/proyectos_cliente/',
            'supabase_table': 'proyectos_cliente'
        },
        {
            'name': 'v_insumos',
            'apex_url': 'https://gsn.maxapex.net/apex/savio/v_insumos/',
            'supabase_table': 'v_insumos'
        }
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"📊 Verificando: {endpoint['name']}")
        print(f"   APEX URL: {endpoint['apex_url']}")
        print(f"   Supabase: {endpoint['supabase_table']}")
        
        # Contar en APEX
        print(f"   🔄 Contando registros en APEX...", end='', flush=True)
        apex_count, apex_error = count_apex_records(
            endpoint['apex_url'],
            apex_username,
            apex_password
        )
        
        if apex_error:
            print(f" ❌ Error: {apex_error}")
            apex_count = 0
        else:
            print(f" ✅ {apex_count:,} registros")
        
        # Contar en Supabase
        print(f"   🔄 Contando registros en Supabase...", end='', flush=True)
        supabase_count, supabase_error = count_supabase_records(
            supabase,
            endpoint['supabase_table']
        )
        
        if supabase_error:
            print(f" ❌ Error: {supabase_error}")
            supabase_count = 0
        else:
            print(f" ✅ {supabase_count:,} registros")
        
        # Calcular diferencia
        if apex_count is not None and supabase_count is not None:
            diff = apex_count - supabase_count
            diff_pct = (supabase_count / apex_count * 100) if apex_count > 0 else 0
            
            if diff == 0:
                status = "✅ SINCRONIZADO"
            elif diff > 0:
                status = f"⚠️  FALTAN {diff:,} registros ({diff_pct:.1f}% sincronizado)"
            else:
                status = f"⚠️  EXCESO de {abs(diff):,} registros"
        else:
            status = "❌ ERROR EN CONTEO"
            diff = None
            diff_pct = None
        
        print(f"   {status}")
        print()
        
        results.append({
            'name': endpoint['name'],
            'apex': apex_count,
            'supabase': supabase_count,
            'diff': diff,
            'pct': diff_pct,
            'status': status
        })
    
    # Resumen final
    print("=" * 100)
    print("📈 RESUMEN DE SINCRONIZACIÓN")
    print("=" * 100)
    print()
    print(f"{'Endpoint':<25} {'APEX':>12} {'Supabase':>12} {'Diferencia':>12} {'%':>8} {'Estado':<30}")
    print("-" * 100)
    
    for r in results:
        apex_str = f"{r['apex']:,}" if r['apex'] is not None else "ERROR"
        supa_str = f"{r['supabase']:,}" if r['supabase'] is not None else "ERROR"
        diff_str = f"{r['diff']:,}" if r['diff'] is not None else "N/A"
        pct_str = f"{r['pct']:.1f}%" if r['pct'] is not None else "N/A"
        
        print(f"{r['name']:<25} {apex_str:>12} {supa_str:>12} {diff_str:>12} {pct_str:>8} {r['status']:<30}")
    
    print()
    print("=" * 100)
    
    # Conclusión
    all_synced = all(r['diff'] == 0 for r in results if r['diff'] is not None)
    
    if all_synced:
        print("✅ TODOS LOS ENDPOINTS ESTÁN COMPLETAMENTE SINCRONIZADOS")
    else:
        print("⚠️  ALGUNOS ENDPOINTS REQUIEREN SINCRONIZACIÓN")
        print()
        print("💡 Acciones recomendadas:")
        for r in results:
            if r['diff'] and r['diff'] > 0:
                print(f"   - Ejecutar: python sync_endpoint_X.py para {r['name']}")
                print(f"     O ejecutar: python sync_all_endpoints.py")
    
    print("=" * 100)
    
    return 0 if all_synced else 1


if __name__ == "__main__":
    sys.exit(main())
