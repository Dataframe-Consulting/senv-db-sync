# Log Vidrios Producción - Guía de Uso

⚠️ **IMPORTANTE**: Este controller maneja un volumen masivo de datos (265,000+ registros históricos).

## 🚀 Modos de Sincronización

### 1. Sincronización Incremental (Recomendado) ⭐

Sincroniza solo los registros nuevos o modificados desde la última sincronización.

```python
from controllers import log_vidrios_produccion

# Automático: usa la última fecha de modificación en Supabase
result = log_vidrios_produccion.sync()
```

**Ventajas:**
- ✅ Rápido (segundos en lugar de minutos)
- ✅ Evita timeouts
- ✅ Usa menos recursos
- ✅ Ideal para ejecuciones programadas

### 2. Rango de Fechas Personalizado

Sincroniza un periodo específico.

```python
from controllers import log_vidrios_produccion

# Última semana
result = log_vidrios_produccion.sync(
    fecha_desde='2026-01-15',
    fecha_hasta='2026-01-23'
)

# Solo desde una fecha hasta hoy
result = log_vidrios_produccion.sync(fecha_desde='2026-01-01')
```

### 3. Primera Sincronización

Si no hay datos previos en Supabase, sincroniza los últimos N días.

```python
from controllers import log_vidrios_produccion

# Últimos 7 días (si es primera vez)
result = log_vidrios_produccion.sync(dias_historico=7)

# Últimos 30 días (si es primera vez)
result = log_vidrios_produccion.sync(dias_historico=30)
```

### 4. Sincronización Completa ⚠️

**Solo usar en casos especiales** (carga inicial, recuperación de datos, etc.)

```python
from controllers import log_vidrios_produccion

# ⚠️ Sincroniza TODOS los registros históricos (puede tardar varios minutos)
result = log_vidrios_produccion.sync(full_sync=True)
```

## 📊 Estadísticas de Datos

- **Registros históricos totales**: ~265,000+
- **Registros típicos por día**: ~700-1,500
- **Tiempo sincronización incremental**: 5-15 segundos
- **Tiempo sincronización completa**: 3-5 minutos (con timeout de 180s)

## 🔄 Uso en Producción

### GitHub Actions (Recomendado)

```yaml
# .github/workflows/sync-log-vidrios.yml
name: Sync Log Vidrios Producción

on:
  schedule:
    # Cada hora
    - cron: '0 * * * *'
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Sync incremental
        env:
          ORACLE_APEX_BASE_URL: ${{ secrets.ORACLE_APEX_BASE_URL }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}
        run: |
          python -c "from controllers import log_vidrios_produccion; log_vidrios_produccion.sync()"
```

### Script Manual

```python
# scripts/sync_log_vidrios.py
from controllers import log_vidrios_produccion
from datetime import datetime

print(f"Iniciando sincronización: {datetime.now()}")
result = log_vidrios_produccion.sync(verbose=True)

if result['success']:
    print(f"\n✅ Éxito: {result['records_synced']:,} registros sincronizados")
    print(f"   Tipo: {result['sync_type']}")
    print(f"   Duración: {result['duration_seconds']:.1f}s")
else:
    print(f"\n❌ Error: {result['error']}")
```

## 🧪 Test sin Sincronizar

Para validar datos antes de sincronizar:

```bash
# Últimos 23 días
python controllers/log_vidrios_produccion/test_data.py 2026-01-01 2026-01-23

# Todos los registros (⚠️ puede tardar varios minutos)
python controllers/log_vidrios_produccion/test_data.py
```

## 📝 Estructura de Datos

Cada registro captura un cambio en el estado de un vidrio en producción:

```json
{
  "id": "10175_25110069_1_9_NO_ETAPA_2026-01-02T13:57:15Z",
  "no_orden_produccion": 10175,
  "no_cotizacion": 25110069,
  "dec_seq": 1,
  "vip_seq": 9,
  "campo": "NO_ETAPA",
  "valor_anterior": "5",
  "valor_nuevo": "8",
  "usr_modif": "GTENORIO",
  "fec_modif": "2026-01-02 13:57:15",
  "fec_modif_pre": "2025-12-16 19:42:08"
}
```

## 🔧 Troubleshooting

### Timeout en sincronización completa

**Solución**: Usa sincronización incremental o por rangos de fechas

```python
# En lugar de:
result = log_vidrios_produccion.sync(full_sync=True)  # ❌ Puede dar timeout

# Usa:
result = log_vidrios_produccion.sync()  # ✅ Incremental
# o
result = log_vidrios_produccion.sync(fecha_desde='2026-01-01')  # ✅ Rango
```

### No se sincronizan registros nuevos

**Verificar**:
1. ¿Hay registros en el rango de fechas?
2. ¿La última fecha en Supabase es correcta?

```python
from controllers.log_vidrios_produccion.components import synchronize

# Ver información actual
info = synchronize.get_last_sync_info(verbose=True)
print(f"Última modificación: {info['last_modified']}")
print(f"Total registros: {info['total_records']}")
```

## 💡 Mejores Prácticas

1. ✅ **Usar sincronización incremental** para ejecuciones regulares
2. ✅ **Programar cada hora** para mantener datos actualizados
3. ✅ **Monitorear duración** de las sincronizaciones
4. ✅ **Usar test_data.py** antes de cambios importantes
5. ❌ **Evitar full_sync** en producción (solo para casos especiales)
