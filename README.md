# Sincronización ERP APEX → Supabase

Sistema de sincronización automática de datos desde Oracle APEX (ERP SAVIO) hacia Supabase PostgreSQL, ejecutándose cada hora mediante GitHub Actions.

## 📋 Problema que Resuelve

Mantiene actualizada una base de datos Supabase con datos del ERP SAVIO, extrayendo información de 4 endpoints y sincronizándola automáticamente **sin duplicados**.

## 🏗️ Arquitectura

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Oracle APEX    │─────▶│  GitHub Actions  │─────▶│   Supabase      │
│  (ERP SAVIO)    │      │  (cada 60 min)   │      │   PostgreSQL    │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

### Componentes

- **Oracle APEX Client**: Extrae datos de los endpoints REST
- **Supabase Client**: Inserta datos con UPSERT para evitar duplicados
- **Sync Service**: Orquesta la sincronización de los 4 endpoints
- **Transformations**: Adapta los datos al formato requerido

## 📊 Endpoints Sincronizados

| # | Endpoint | Tabla Supabase | Descripción | Script |
|---|----------|----------------|-------------|--------|
| 1 | `v_log_cambios_etapa` | `log_cambios_etapa` | Cambios de etapa en producción | `sync_endpoint_1.py` |
| 2 | `detalle_cotizacion` | `detalle_cotizacion` | Detalles de cotizaciones | `sync_endpoint_2.py` |
| 3 | `vidrios_produccion` | `vidrios_produccion` | Vidrios en producción | `sync_endpoint_3.py` |
| 4 | `log_vidrios_produccion` | `log_vidrios_produccion` | Log de vidrios producidos | `sync_endpoint_4.py` |
| 5 | `cotizaciones` | `cotizaciones` | Cotizaciones generales | `sync_endpoint_5.py` |
| 6 | `clientes` | `clientes` | Catálogo de clientes | `sync_endpoint_6.py` |
| 7 | `proyectos_cliente` | `proyectos_cliente` | Proyectos por cliente | `sync_endpoint_7.py` |
| 8 | `v_insumos` | `v_insumos` | Catálogo de insumos | `sync_endpoint_8.py` |

## 🚀 Características

- ✅ **Sincronización automática cada hora** mediante GitHub Actions
- ✅ **Prevención de duplicados** usando UPSERT con PRIMARY KEY
- ✅ **Procesamiento por lotes** para eficiencia
- ✅ **Manejo de errores** con reintentos automáticos
- ✅ **Logs detallados** de cada sincronización
- ✅ **Solo datos nuevos** se agregan a Supabase

## 🔄 Flujo de Sincronización

1. **Extracción**: Obtiene datos de Oracle APEX por lotes
2. **Transformación**: Adapta el formato y genera IDs únicos
3. **Validación**: Verifica que no existan duplicados
4. **Inserción**: Usa UPSERT en Supabase (`INSERT ... ON CONFLICT DO UPDATE`)
5. **Reporte**: Genera logs con estadísticas

## 🚀 Ejecución Local

### 1. Configurar entorno

```bash
# Clonar repositorio
git clone https://github.com/Dataframe-Consulting/senv-apex-db-sync.git
cd senv-apex-db-sync

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

Crear archivo `.env`:

```env
ORACLE_APEX_USERNAME=tu_usuario
ORACLE_APEX_PASSWORD=tu_contraseña
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=tu_clave_supabase
```

### 3. Ejecutar sincronización

```bash
# Sincronizar todos los endpoints (los 4 a la vez)
python sync_all_endpoints.py
```

## ⚙️ GitHub Actions (Automático cada hora)

### Paso 1: Crear las tablas en Supabase

Antes de ejecutar el workflow, crea las tablas en Supabase:

1. Ve al editor SQL de Supabase
2. Ejecuta el script `scripts/create_all_tables.sql`
3. Verifica que las 4 tablas se crearon correctamente

### Paso 2: Configurar Environment en GitHub

1. Ve a: `Settings → Environments → New environment`
2. Nombre: `production` (o el que prefieras)
3. Haz clic en "Configure environment"

### Paso 3: Agregar Secrets al Environment

En la sección "Environment secrets", agrega los siguientes secrets:

| Secret | Descripción | Ejemplo |
|--------|-------------|---------|
| `ORACLE_APEX_BASE_URL` | URL base del Oracle APEX | `https://gsn.maxapex.net/ords/savio` |
| `ORACLE_APEX_USERNAME` | Usuario de Oracle APEX | Tu usuario |
| `ORACLE_APEX_PASSWORD` | Contraseña de Oracle APEX | Tu contraseña |
| `SUPABASE_URL` | URL de tu proyecto Supabase | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | API Key de Supabase | Tu clave anon/service_role |
| `SUPABASE_DB_PASSWORD` | Contraseña DB Supabase | Tu contraseña de DB |

### Paso 4: Ejecutar el Workflow

El workflow `.github/workflows/sync-erp-data.yml` se ejecuta:
- **Automáticamente**: Cada 60 minutos (cron: `0 * * * *`)
- **Manualmente**: Desde la pestaña "Actions" en GitHub

Los **4 endpoints se sincronizan en una sola ejecución** para mantener la consistencia.

## 🔒 Prevención de Duplicados

El sistema usa **UPSERT** con la columna `id` como PRIMARY KEY:

```python
supabase_client.batch_upsert(
    transformed_data,
    conflict_column='id'
)
```

Esto garantiza que:
- Si el registro existe (mismo `id`), se actualiza
- Si no existe, se inserta nuevo
- **No se crean duplicados**

## 📈 Rendimiento

- **Velocidad promedio**: 50-350 registros/segundo
- **Batch size**: 100 registros por lote
- **Tiempo estimado**: 2-3 horas para sincronización completa inicial

## 🆕 Nuevos Endpoints (Diciembre 2025)

Se agregaron **4 nuevos endpoints** al sistema de sincronización:

### Cotizaciones (`cotizaciones`)
- 19 campos + metadatos
- ID único: `no_cotizacion`
- Incluye: fechas, clientes, proyectos, status, moneda

### Clientes (`clientes`)
- 22 campos + metadatos
- ID único: `no_cliente`
- Incluye: RFC, razón social, régimen fiscal, contactos

### Proyectos Cliente (`proyectos_cliente`)
- 12 campos + metadatos
- ID compuesto: `{no_cliente}_{no_proyecto}`
- Incluye: nombres, anticipos, Skyplanner ID

### Vista Insumos (`v_insumos`)
- 24 campos + metadatos
- ID único: `no_insumo`
- Incluye: claves, descripciones, precios (MXN/USD/EUR), tiempos

### 📚 Documentación Detallada

Para más información sobre los nuevos endpoints:
- **Guía de configuración**: `docs/NUEVOS_ENDPOINTS.md`
- **Resumen técnico**: `docs/RESUMEN_IMPLEMENTACION.md`
- **Inicio rápido**: `docs/INICIO_RAPIDO.md`

### ⚠️ Importante

Para activar los nuevos endpoints, **debes ejecutar primero** el script SQL:
```bash
scripts/create_new_tables.sql
```

## 🛠️ Tecnologías

- **Python 3.11**
- **Supabase** (PostgreSQL)
- **Oracle APEX REST**
- **GitHub Actions**
- **Librerías**: `supabase-py`, `requests`, `python-dotenv`

## 📞 Soporte

**Dataframe Consulting**  
Última actualización: 10 de diciembre de 2025
