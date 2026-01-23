# Controller: Clientes

## 📋 Descripción

Sincroniza catálogo de clientes desde el ERP SAVIO a Supabase.

## 🌐 Endpoint

**URL:** `https://gsn.maxapex.net/apex/savio/clientes`

## ❌ Limitaciones

- **No soporta filtrado por fecha**
- Descarga completa en cada sincronización

## 🔄 Estrategia

**Tipo:** Full Sync Idempotente (UPSERT por `no_cliente`)

## 📊 Volumen

- **Registros:** ~50 clientes
- **Crecimiento:** Bajo (~1-2/mes)
- **Tiempo:** <5 segundos

## 🔑 Primary Key

- `no_cliente` (Integer, único)

## 🔗 Dependencias

- **Downstream:** `cotizaciones`, `proyectos_cliente`

## 📅 Frecuencia Recomendada

- Cada 6-12 horas (datos cambian poco)
