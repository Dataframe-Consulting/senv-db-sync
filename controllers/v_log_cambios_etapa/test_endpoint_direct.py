"""
Prueba del endpoint directo /v_log_cambios_etapa.

Verifica:
 1. Que el endpoint responde
 2. Estructura del response (hasMore, items, etc.)
 3. Primeras páginas con paginación
 4. Estimación del total de registros

Uso:
    python test_endpoint_direct.py          # Prueba 5 páginas
    python test_endpoint_direct.py 20       # Prueba N páginas
"""

import sys
import os
import time

# Ajustar path para imports desde raíz del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from utils.http_client import http_get

BASE_URL = os.getenv('ORACLE_APEX_BASE_URL', 'https://gsn.maxapex.net/apex/savio')
ENDPOINT = f"{BASE_URL}/v_log_cambios_etapa"
LIMIT = 1000

def test_endpoint(max_pages: int = 5):
    print(f"\n{'='*60}")
    print(f"🔍 TEST: Endpoint directo /v_log_cambios_etapa")
    print(f"{'='*60}")
    print(f"URL: {ENDPOINT}")
    print(f"Páginas a probar: {max_pages}")
    print()

    # --- Página 1: verificar estructura ---
    print("📄 Página 1 (offset=0)...")
    t0 = time.time()
    data, success = http_get(ENDPOINT, params={'limit': LIMIT, 'offset': 0}, verbose=True)
    elapsed = time.time() - t0

    if not success or data is None:
        print("❌ El endpoint no respondió correctamente")
        return

    print(f"   ⏱️  Tiempo respuesta: {elapsed:.2f}s")

    # Estructura del response
    if isinstance(data, dict):
        keys = list(data.keys())
        print(f"   📦 Estructura response (dict): keys={keys}")
        has_more = data.get('hasMore', 'N/A')
        count    = data.get('count', 'N/A')
        items    = data.get('items') or data.get('rows') or data.get('data') or []
        print(f"   hasMore: {has_more}")
        print(f"   count:   {count}")
        print(f"   items:   {len(items):,} registros en esta página")
    elif isinstance(data, list):
        items = data
        has_more = len(items) == LIMIT  # asumir si devuelve página llena
        print(f"   📦 Estructura response (list): {len(items):,} registros")
        print(f"   hasMore inferido: {has_more}")
    else:
        print(f"   ⚠️  Tipo inesperado: {type(data)}")
        return

    if not items:
        print("   ⚠️  No hay registros en la primera página")
        return

    # Muestra un registro de ejemplo
    print(f"\n   🔑 Campos disponibles: {list(items[0].keys())}")
    print(f"   📝 Primer registro: {items[0]}")

    # --- Páginas adicionales ---
    total = len(items)
    tiempos = [elapsed]

    for page in range(2, max_pages + 1):
        offset = (page - 1) * LIMIT
        t0 = time.time()
        data, success = http_get(ENDPOINT, params={'limit': LIMIT, 'offset': offset}, verbose=False)
        elapsed = time.time() - t0
        tiempos.append(elapsed)

        if not success or data is None:
            print(f"   ❌ Error en página {page}")
            break

        if isinstance(data, dict):
            page_items = data.get('items') or data.get('rows') or data.get('data') or []
            has_more = data.get('hasMore', False)
        else:
            page_items = data if isinstance(data, list) else []
            has_more = len(page_items) == LIMIT

        total += len(page_items)
        print(f"   📄 Página {page:>4} (offset {offset:>8,}): {len(page_items):>5,} registros | "
              f"⏱️ {elapsed:.2f}s | hasMore={has_more}")

        if not has_more or not page_items:
            print("   ✅ Fin de datos (hasMore=False)")
            break

    # --- Resumen y estimación ---
    avg_time = sum(tiempos) / len(tiempos)
    pages_tested = len(tiempos)

    print(f"\n{'='*60}")
    print(f"📊 RESUMEN")
    print(f"{'='*60}")
    print(f"   Páginas probadas:       {pages_tested}")
    print(f"   Registros obtenidos:    {total:,}")
    print(f"   Tiempo promedio/página: {avg_time:.2f}s")
    print(f"   Tiempo total prueba:    {sum(tiempos):.1f}s")

    # Si hasMore sigue activo en la última página, estimar
    if has_more:
        print(f"\n   ⚠️  El endpoint tiene MÁS páginas. Estimaciones si sigue paginando:")
        for total_est in [1_000_000, 10_000_000, 50_000_000, 106_000_000]:
            pages_est = total_est // LIMIT
            time_est_h = (pages_est * avg_time) / 3600
            print(f"      {total_est/1_000_000:.0f}M registros → ~{pages_est:,} páginas → ~{time_est_h:.1f}h")
    else:
        print(f"\n   ✅ Dataset completo obtenido en {pages_tested} páginas")

if __name__ == '__main__':
    max_pages = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    test_endpoint(max_pages)
