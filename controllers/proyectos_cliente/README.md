# Controller: Proyectos Cliente

## 📋 Descripción

Proyectos asociados a clientes

## 🌐 Endpoint

**URL:** `https://gsn.maxapex.net/apex/savio/proyectos_cliente`

## ❌ Limitaciones

- **No soporta filtrado por fecha**
- Descarga completa en cada sincronización

## 🔄 Estrategia

**Tipo:** Full Sync Idempotente (UPSERT por ID)

## 📊 Volumen

- **Registros:** ~250 proyectos
- **Tiempo:** Variable según volumen

## 🔑 Primary Key

- Campos: `no_cliente, no_proyecto`

## 📅 Frecuencia Recomendada

- 6-12 horas
