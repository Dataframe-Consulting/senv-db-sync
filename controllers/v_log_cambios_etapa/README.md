# Controller: V Log Cambios Etapa

## 📋 Descripción

Log de cambios de etapa en producción. Registra cada cambio de estado/etapa por orden de producción.

## 🌐 Endpoint

**Patrón:** `https://gsn.maxapex.net/apex/savio/periodo/cambios_etapa/{no_orden_produccion}`

**Tipo:** Endpoint por orden de producción individual

## 🔄 Estrategia de Sincronización

### ⭐ Sincronización Inteligente (Incremental Real)

Este controller implementa una estrategia de **sincronización incremental verdadera**:

1. **Consultar Supabase** para obtener la fecha de última modificación (`fec_modif`)
2. **Obtener órdenes de producción** de `log_vidrios_produccion` desde esa fecha
3. **Consultar cambios de etapa** para cada orden obtenida

**Modos de sincronización:**
- **INCREMENTAL (default):** Consulta Supabase y sincroniza solo desde la última fecha
- **FULL SYNC:** Ignora Supabase y sincroniza últimos N días completos (configurable)
- **MANUAL:** Especifica fechas manualmente

### Ventajas vs Enfoque Anterior

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Fuente de órdenes** | `vidrios_produccion` (97K registros) | `log_vidrios_produccion` con filtro (15K) |
| **Órdenes a consultar** | ~2,093 órdenes (históricas) | ~500 órdenes (activas últimos 30 días) |
| **Duración estimada** | 2-3 horas | 15-30 minutos |
| **Datos relevantes** | Incluye órdenes antiguas/cerradas | Solo órdenes recientes/activas |
| **Estado por defecto** | DESHABILITADO (muy lento) | HABILITADO (optimizado) |

## 📊 Volumen

- **Órdenes consultadas:** ~500 (últimos 30 días)
- **Registros por orden:** 5-10 cambios promedio
- **Total registros:** ~2,500-5,000 cambios
- **Tiempo estimado:** 15-30 minutos

## 🚀 Uso

### 1. Sincronización Incremental (Recomendado)

```python
from controllers import v_log_cambios_etapa

# Incremental: consulta Supabase y sincroniza desde última fecha
result = v_log_cambios_etapa.run()
```

**¿Cómo funciona?**
1. Consulta `log_cambios_etapa` en Supabase
2. Obtiene la fecha máxima de `fec_modif`
3. Sincroniza solo cambios desde esa fecha hasta hoy
4. Si no hay datos en Supabase (primera vez), usa últimos 30 días

### 2. Sincronización Full (Últimos N días)

```python
from controllers import v_log_cambios_etapa

# Full sync: últimos 30 días (ignora fecha en Supabase)
result = v_log_cambios_etapa.sync(full_sync=True)

# Full sync: últimos 7 días
result = v_log_cambios_etapa.sync(full_sync=True, dias_historico=7)

# Full sync: últimos 60 días
result = v_log_cambios_etapa.sync(full_sync=True, dias_historico=60)
```

### 3. Sincronización Manual (Fechas Específicas)

```python
from controllers import v_log_cambios_etapa

# Rango específico
result = v_log_cambios_etapa.sync(
    fecha_desde='2026-01-01',
    fecha_hasta='2026-01-23'
)

# Desde fecha hasta hoy
result = v_log_cambios_etapa.sync(fecha_desde='2026-01-01')
```

### Test sin Sincronizar

```bash
# Incremental: consulta Supabase (recomendado)
python controllers/v_log_cambios_etapa/test_data.py

# Full sync: últimos 30 días completos
python controllers/v_log_cambios_etapa/test_data.py --full

# Rango específico
python controllers/v_log_cambios_etapa/test_data.py 2026-01-01 2026-01-23

# Desde fecha hasta hoy
python controllers/v_log_cambios_etapa/test_data.py 2026-01-01
```

## 🔑 Primary Key

```python
id = f"{no_orden_produccion}_{dec_seq}_{vip_seq}_{no_etapa}"
```

**Campos que conforman el ID:**
- `no_orden_produccion`: Número de orden
- `dec_seq`: Secuencia DEC
- `vip_seq`: Secuencia VIP
- `no_etapa`: Número de etapa

## 📅 Frecuencia Recomendada

- **Producción:** Cada 1 hora (modo incremental automático)
- **Primera ejecución:** Últimos 30 días automáticamente
- **Ejecuciones posteriores:** Solo cambios nuevos desde última sincronización
- **Desarrollo/Testing:** Manual con rangos específicos

## ⚙️ Configuración

### Parámetros de sync()

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `fecha_desde` | str | None | Fecha inicial (YYYY-MM-DD) - si se especifica, modo MANUAL |
| `fecha_hasta` | str | None | Fecha final (YYYY-MM-DD) |
| `dias_historico` | int | 30 | Días hacia atrás para full_sync o primera sincronización |
| `full_sync` | bool | False | Si True, ignora fecha en Supabase y usa dias_historico |
| `verbose` | bool | True | Mostrar logs de progreso |

### Lógica de Determinación de Fechas

```python
if fecha_desde:
    # MODO MANUAL: Usa la fecha especificada
    modo = "manual"
elif full_sync:
    # MODO FULL: Últimos N días (ignora Supabase)
    fecha_desde = hoy - dias_historico
elif supabase_tiene_datos:
    # MODO INCREMENTAL: Desde última fecha en Supabase
    fecha_desde = max(fec_modif) en log_cambios_etapa
else:
    # PRIMERA SINCRONIZACIÓN: Últimos N días
    fecha_desde = hoy - dias_historico
```

## 🔍 Dependencias

Este controller depende de:
- `log_vidrios_produccion` - Para obtener órdenes de producción recientes
- Endpoint `periodo/cambios_etapa/{op}` - Para obtener cambios por orden

## 📈 Performance

| Métrica | Valor |
|---------|-------|
| **Órdenes/segundo** | ~0.5-1 orden/segundo |
| **Timeout por orden** | 60 segundos |
| **Órdenes típicas (30 días)** | ~500 |
| **Duración total estimada** | 15-30 minutos |

## ⚠️ Notas Importantes

1. **Sincronización Incremental Real:** Consulta Supabase para saber desde qué fecha sincronizar
2. **Eficiencia:** Usa `log_vidrios_produccion` con filtro de fecha para obtener solo órdenes activas
3. **Sin Re-procesamiento:** Solo sincroniza cambios nuevos (desde última `fec_modif` en Supabase)
4. **Primera Sincronización:** Si Supabase está vacío, sincroniza últimos 30 días automáticamente
5. **Idempotencia:** Usa UPSERT, puede re-ejecutarse sin duplicar datos
6. **Timeout:** Configurado a 60s por orden (normalmente responde en <5s)
7. **Habilitado por defecto:** Está habilitado en `sync_main.py` con modo incremental

## 🐛 Troubleshooting

### "Tomó demasiado tiempo"

Si la sincronización toma >1 hora:
- Reducir `dias_historico` a 7 o 15 días
- Verificar que `log_vidrios_produccion` esté usando filtro de fecha correctamente

### "No se obtuvieron órdenes"

Verificar que `log_vidrios_produccion` tenga datos:
```python
from controllers.log_vidrios_produccion.components import get_data as log_get_data
logs, success = log_get_data.fetch_all(fecha_desde='2026-01-01', verbose=True)
print(f"Registros en log_vidrios: {len(logs)}")
```

## 📚 Documentación Adicional

Ver `USAGE.md` en el directorio raíz para ejemplos más detallados.
