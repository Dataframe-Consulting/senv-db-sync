# Controller: Detalle Cotizacion

## 📋 Descripción

Detalles de cotizaciones (líneas de productos)

## 🌐 Endpoint

**URL:** `https://gsn.maxapex.net/apex/savio/detalle_cotizacion`

## ❌ Limitaciones

- **No soporta filtrado por fecha**
- Descarga completa en cada sincronización

## 🔄 Estrategia

**Tipo:** Full Sync Idempotente (UPSERT por ID)

## 📊 Volumen

- **Registros:** ~20,000 detalles
- **Tiempo:** Variable según volumen

## 🔑 Primary Key

- Campos: `no_cotizacion, dec_seq, renglon`

## 📅 Frecuencia Recomendada

- 1-2 horas
