# Controller: V Log Cambios Etapa

## 📋 Descripción

Log de cambios de etapa en producción. Registra cada evento de cambio de estado/etapa por orden de producción. La tabla es un **clon fiel del origen** — cada fila representa un evento histórico distinto.

## 🌐 Endpoints

| Modo | URL | Cuándo se usa |
|------|-----|---------------|
| **Carga completa** | `/v_log_cambios_etapa` | Tabla vacía (primera carga) |
| **Incremental** | `/periodo/cambios_etapa/{no_orden}` | Ejecuciones normales (por orden) |

## 🔄 Estrategia de Sincronización

### Lógica de decisión automática

```
Tabla vacía (0 registros)
    → Endpoint directo /v_log_cambios_etapa
    → Modo STREAMING: pagina → transforma → upsert (sin acumular en RAM)
    → Carga TODO el histórico disponible

Tabla con datos
    → Obtiene max(fec_modif) de Supabase
    → Filtra órdenes en log_vidrios_produccion desde esa fecha
    → Consulta /periodo/cambios_etapa/{op} para cada orden
    → Modo INCREMENTAL: solo novedades
```

**Modos de sincronización:**
- **CARGA COMPLETA (tabla vacía):** Endpoint directo + streaming, sin límite de RAM
- **INCREMENTAL (default):** Desde `max(fec_modif)` en Supabase
- **FULL SYNC:** Últimos N días via endpoint por orden (ignora fecha en Supabase)
- **MANUAL:** Fechas especificadas por parámetro

## 🔑 Primary Key

```python
id = f"{no_orden_produccion}_{dec_seq}_{vip_seq}_{no_etapa}_{fec_modif}"
```

El ID incluye `fec_modif` para preservar **todos los eventos** de un vidrio en una etapa como filas independientes. Si el mismo vidrio pasa dos veces por la misma etapa (reproceso), ambos eventos quedan en la tabla.

La deduplicación solo elimina filas **exactamente repetidas** devueltas por el API.

## 📊 Volumen

| Escenario | Registros | Tiempo estimado |
|-----------|-----------|-----------------|
| Incremental diario | ~27K novedades | ~30s |
| Carga completa histórica | ~106M | ~17-25h (streaming) |

## 🚀 Uso

### 1. Sincronización Incremental (Recomendado para producción)

```python
from controllers import v_log_cambios_etapa

result = v_log_cambios_etapa.run()
```

### 2. Carga completa histórica (tabla vacía)

Borrar la tabla por SQL en Supabase y luego ejecutar normalmente. El controller detecta tabla vacía y activa el modo streaming automáticamente:

```bash
# Desde directorio raíz
python controllers/v_log_cambios_etapa/test_data.py
```

```python
# O desde código
result = v_log_cambios_etapa.run()  # detecta tabla vacía → carga completa
```

### 3. Full Sync (últimos N días via endpoint por orden)

```python
result = v_log_cambios_etapa.sync(full_sync=True)                  # últimos 30 días
result = v_log_cambios_etapa.sync(full_sync=True, dias_historico=7)
result = v_log_cambios_etapa.sync(full_sync=True, dias_historico=60)
```

### 4. Rango manual

```python
result = v_log_cambios_etapa.sync(
    fecha_desde='2026-01-01',
    fecha_hasta='2026-01-31'
)
```

### Test del endpoint directo

```bash
# Prueba 5 páginas (default)
python controllers/v_log_cambios_etapa/test_endpoint_direct.py

# Prueba N páginas y estima tiempo total
python controllers/v_log_cambios_etapa/test_endpoint_direct.py 20
```

### Test de datos (sin sincronizar a Supabase)

```bash
python controllers/v_log_cambios_etapa/test_data.py          # incremental
python controllers/v_log_cambios_etapa/test_data.py --full   # full sync 30 días
python controllers/v_log_cambios_etapa/test_data.py 2026-01-01 2026-01-31
```

## ⚙️ Parámetros de sync()

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `fecha_desde` | str | None | Fecha inicial (YYYY-MM-DD) — activa modo MANUAL |
| `fecha_hasta` | str | None | Fecha final (YYYY-MM-DD) |
| `dias_historico` | int | 30 | Días hacia atrás para `full_sync` |
| `full_sync` | bool | False | Ignora fecha en Supabase, usa `dias_historico` |
| `verbose` | bool | True | Mostrar logs de progreso |

## 📈 Performance

| Métrica | Valor |
|---------|-------|
| **Velocidad endpoint directo** | ~0.6s/página (1,000 registros/página) |
| **Velocidad endpoint por orden** | ~0.5-1 orden/segundo |
| **RAM carga completa** | Constante (~1,000 registros en memoria) |
| **Timeout por página/orden** | 120s (carga completa) / 60s (incremental) |

## 🔍 Dependencias

- `log_vidrios_produccion` — fuente de órdenes para modo incremental
- `/v_log_cambios_etapa` — endpoint directo para carga completa
- `/periodo/cambios_etapa/{op}` — endpoint por orden para incremental

## ⚠️ Notas Importantes

1. **Clon fiel:** Cada fila en Supabase es un evento histórico, no el "estado actual"
2. **ID con fecha:** Incluye `fec_modif` — mismo vidrio/etapa con distinta fecha = filas distintas
3. **Streaming:** La carga completa no acumula en RAM; procesa y sube página a página
4. **Idempotente:** Usa UPSERT; re-ejecutar no genera duplicados
5. **Tabla vacía:** Detectada automáticamente — no requiere parámetro especial

## 🐛 Troubleshooting

### Repoblar la tabla desde cero

```sql
-- En Supabase SQL Editor
TRUNCATE TABLE log_cambios_etapa;
```

Luego ejecutar el sync normalmente. Detectará tabla vacía y hará carga completa vía streaming.

### Verificar endpoint directo

```bash
python controllers/v_log_cambios_etapa/test_endpoint_direct.py 3
```

### Verificar órdenes disponibles para incremental

```python
from controllers.log_vidrios_produccion.components import get_data as log_get_data
logs, success = log_get_data.fetch_all(fecha_desde='2026-01-01', verbose=True)
print(f"Registros en log_vidrios: {len(logs)}")
```
