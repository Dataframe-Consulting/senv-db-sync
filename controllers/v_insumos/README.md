# Controller: V Insumos

## 📋 Descripción

Catálogo de insumos y materiales

## 🌐 Endpoint

**URL:** `https://gsn.maxapex.net/apex/savio/v_insumos`

## ❌ Limitaciones

- **No soporta filtrado por fecha**
- Descarga completa en cada sincronización

## 🔄 Estrategia

**Tipo:** Full Sync Idempotente (UPSERT por ID)

## 📊 Volumen

- **Registros:** ~300 insumos
- **Tiempo:** Variable según volumen

## 🔑 Primary Key

- Campos: `no_insumo`

## 📅 Frecuencia Recomendada

- 12-24 horas
