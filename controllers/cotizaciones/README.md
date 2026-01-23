# Controller: Cotizaciones

## 📋 Descripción

Sincroniza datos de cotizaciones desde el ERP SAVIO a Supabase.

## 🌐 Endpoint

**URL Base:** `https://gsn.maxapex.net/apex/savio/cotizaciones`

**Estructura del endpoint:**
- URL completa retorna TODAS las cotizaciones (sin paginación explícita en el endpoint)
- No soporta parámetros de paginación estándar
- No soporta filtrado por fecha

## ❌ Limitaciones

### No Soporta Filtro por Fecha

Este endpoint **NO acepta parámetros de filtrado por fecha**. Razones:

1. La API de Oracle APEX para este endpoint no expone parámetros de filtrado
2. Intentos de usar `q={"fec_modif":{"$gte":"..."}}` retornan 0 registros
3. El endpoint está diseñado para descarga completa

### Consecuencias

- Cada sincronización descarga **TODAS** las cotizaciones
- No es posible sincronización incremental por fecha
- Se confía en **UPSERT** para evitar duplicados

## 🔄 Estrategia de Sincronización

**Tipo:** Full Sync Idempotente

1. Descargar todas las cotizaciones del endpoint
2. Transformar a formato Supabase
3. UPSERT usando `no_cotizacion` como clave primaria
4. Los registros existentes se actualizan, los nuevos se insertan

## 📊 Volumen de Datos

- **Registros actuales:** ~2,500 cotizaciones
- **Crecimiento:** ~50-100 cotizaciones/mes
- **Tiempo de sync:** ~5-10 segundos
- **Ancho de banda:** ~500KB por sync

## 🔑 Primary Key

- **Campo ID:** `no_cotizacion` (número único de cotización)
- **Tipo:** Integer
- **Generado por:** ERP SAVIO (autoincremental)

## 📦 Estructura de Datos

### Campos Principales

- `no_cotizacion`: ID único
- `no_cliente`: Referencia a cliente
- `no_proyecto`: Referencia a proyecto
- `fecha`: Fecha de la cotización
- `status`: Estado (A=Activa, C=Cancelada, etc.)
- `fec_modif`, `usr_modif`: Auditoría

### Campos Calculados

- `pct_descuento`: Porcentaje de descuento
- `no_orden_compra`: Número de OC del cliente

## 🔗 Dependencias

### Prerequisitos

Ninguno - Este endpoint es independiente

### Dependencias Downstream

Los siguientes endpoints dependen de cotizaciones:

- `detalle_cotizacion` (require `no_cotizacion`)
- `vidrios_produccion` (require `no_cotizacion`)

## ⚡ Consideraciones de Performance

- **Bajo impacto:** Volumen pequeño de datos
- **Sin rate limiting:** Se puede ejecutar cada hora
- **Idempotente:** Seguro ejecutar múltiples veces

## 📅 Frecuencia Recomendada

- **Producción:** Cada 1-2 horas
- **Desarrollo:** Bajo demanda
- **Crítico:** No - los datos no cambian frecuentemente

## 🧪 Testing

### Endpoint de prueba

```bash
curl https://gsn.maxapex.net/apex/savio/cotizaciones
```

### Validación

- Verificar que retorna JSON con lista de cotizaciones
- Confirmar que todos los registros tienen `no_cotizacion`
- Validar formato de fechas (ISO 8601)

## 📝 Notas Técnicas

- Endpoint público (sin autenticación)
- Response format: JSON array o `{items: [...]}`
- Encoding: UTF-8
- Sin límite de resultados (retorna todos)
