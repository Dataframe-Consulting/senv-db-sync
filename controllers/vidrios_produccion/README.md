# Controller: Vidrios Produccion

## 📋 Descripción

Vidrios en producción

## 🌐 Endpoint

**URL:** `https://gsn.maxapex.net/apex/savio/vidrios_produccion`

## ❌ Limitaciones

- **No soporta filtrado por fecha**
- Descarga completa en cada sincronización

## 🔄 Estrategia

**Tipo:** Full Sync Idempotente (UPSERT por ID)

## 📊 Volumen

- **Registros:** ~100,000 vidrios
- **Tiempo:** Variable según volumen

## 🔑 Primary Key

- Campos: `no_orden_produccion, no_cotizacion, dec_seq, vip_seq`

## 📅 Frecuencia Recomendada

- 1 hora
