# Controller: V Log Cambios Etapa

## 📋 Descripción

Log de cambios de etapa en producción

## 🌐 Endpoint

**URL:** `https://gsn.maxapex.net/apex/savio/v_log_cambios_etapa`

## ❌ Limitaciones

- **No soporta filtrado por fecha**
- Descarga completa en cada sincronización

## 🔄 Estrategia

**Tipo:** Full Sync Idempotente (UPSERT por ID)

## 📊 Volumen

- **Registros:** ~30,000 cambios
- **Tiempo:** Variable según volumen

## 🔑 Primary Key

- Campos: `no_orden_produccion, dec_seq, vip_seq, no_etapa`

## 📅 Frecuencia Recomendada

- 1 hora
