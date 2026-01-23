# Controller: Log Vidrios Produccion

## 📋 Descripción

Log de cambios en vidrios de producción

## 🌐 Endpoint

**URL:** `https://gsn.maxapex.net/apex/savio/log_vidrios_produccion`

## ❌ Limitaciones

- **No soporta filtrado por fecha**
- Descarga completa en cada sincronización

## 🔄 Estrategia

**Tipo:** Full Sync Idempotente (UPSERT por ID)

## 📊 Volumen

- **Registros:** ~50,000 logs
- **Tiempo:** Variable según volumen

## 🔑 Primary Key

- Campos: `no_orden_produccion, no_cotizacion, dec_seq, vip_seq, campo, fec_modif`

## 📅 Frecuencia Recomendada

- 1 hora
