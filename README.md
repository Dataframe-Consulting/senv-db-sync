# 🔄 Sincronización ERP APEX → Supabase

Sistema de sincronización automática de datos desde **Oracle APEX (ERP SAVIO)** hacia **Supabase PostgreSQL**, ejecutándose cada 6 horas mediante GitHub Actions.

**Versión:** 2.0 (Sistema Nuevo - Enero 2026)  
**Estado:** ✅ Producción

---

## 📋 Descripción

Mantiene actualizada una base de datos Supabase con datos del ERP SAVIO, sincronizando **8 endpoints** de forma automática, idempotente y escalable.

---

## 🏗️ Arquitectura

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Oracle APEX    │─────▶│  GitHub Actions  │─────▶│   Supabase      │
│  (ERP SAVIO)    │      │  (cada 6 horas)  │      │   PostgreSQL    │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

### Sistema Basado en **Controllers Autónomos**

```
sync_main.py
    ↓
controllers/ (8 endpoints)
├── cotizaciones/
│   ├── README.md                    # Documentación del endpoint
│   ├── cotizaciones.controller.py   # Orquestador
│   └── components/
│       ├── get_data.py              # URL + paginación
│       ├── transform_data.py        # Transformación completa
│       └── synchronize.py           # UPSERT a Supabase
├── clientes/
├── proyectos_cliente/
├── v_insumos/
├── detalle_cotizacion/
├── vidrios_produccion/
├── log_vidrios_produccion/
└── v_log_cambios_etapa/
```

---

## 📊 Endpoints Sincronizados (8 total)

| # | Endpoint | Tabla Supabase | Registros | Páginas | Duración | Tipo |
|---|----------|----------------|-----------|---------|----------|------|
| 1 | `clientes` | `clientes` | 36 | 1 | <1s | Simple ✅ |
| 2 | `proyectos_cliente` | `proyectos_cliente` | 231 | 1 | <1s | Simple ✅ |
| 3 | `v_insumos` | `v_insumos` | 249 | 1 | <1s | Simple ✅ |
| 4 | `cotizaciones` | `cotizaciones` | 2,166 | 3 | ~3s | Simple ✅ |
| 5 | `detalle_cotizacion` | `detalle_cotizacion` | 17,798 | 18 | ~12s | Medio ⚠️ |
| 6 | `vidrios_produccion` | `vidrios_produccion` | 97,826 | 98 | ~80s | Grande ⚠️ |
| 7 | `log_vidrios_produccion` | `log_vidrios_produccion` | 15,498* | 16 | ~5s | Incremental ⭐ |
| 8 | `v_log_cambios_etapa` | `log_cambios_etapa` | Variable** | - | Variable | Especial 🔧 |

**Notas:**
- *log_vidrios_produccion: 15,498 con filtro de 23 días | 265,000+ sin filtro (usa incremental por defecto)
- **v_log_cambios_etapa: Consulta por orden de producción (2,093 órdenes) - DESHABILITADO por defecto

**Total típico por sincronización:** ~133,000 registros en ~2-3 minutos

---

## 🚀 Características

- ✅ **Sincronización automática** cada 6 horas (GitHub Actions)
- ✅ **Paginación automática** - Maneja endpoints con +100K registros
- ✅ **Sin validaciones** - Sistema permisivo (si falta dato → NULL)
- ✅ **UPSERT idempotente** - Sin duplicados
- ✅ **Controllers autónomos** - Cada endpoint independiente
- ✅ **Sin CLI** - Script directo y simple
- ✅ **Escalable** - Agregar endpoint = crear carpeta
- ✅ **Documentado** - README por controller

---

## 🔄 Flujo de Sincronización

Cada controller ejecuta **4 pasos:**

```
1. 📊 Información previa
   └─ Consulta últimos datos en Supabase

2. 📥 Extraer datos
   └─ Obtiene TODOS los registros (paginación automática)

3. 🔄 Transformar
   └─ Convierte al formato de Supabase (campos → NULL si faltan)

4. 💾 Sincronizar
   └─ UPSERT en batches de 1000 registros
```

---

## 🚀 Ejecución Local

### 1. Configurar Entorno

```bash
# Clonar repositorio
git clone https://github.com/tu-org/senv-db-sync.git
cd senv-db-sync

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

Copiar el archivo de ejemplo y completar con valores reales:

```bash
# Copiar el template
cp .env.example .env

# Editar .env con tus credenciales
nano .env  # o vim .env, o el editor que prefieras
```

Variables requeridas en `.env`:

```env
ORACLE_APEX_BASE_URL=https://gsn.maxapex.net/apex/savio
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu_supabase_service_role_key
```

**Solo 3 variables necesarias** (vs 10+ en sistema anterior)

⚠️ **Importante:** Usar la clave `service_role` de Supabase, NO la `anon` key

### 3. Ejecutar Sincronización

```bash
# Sincronizar los 8 endpoints
python sync_main.py
```

**Output esperado:**
```
======================================================================
🔄 CONTROLLER: Cotizaciones
======================================================================

📊 Paso 1/4: Información actual...
   Registros en Supabase: 4,521
   Última actualización: 2026-01-23 08:30:15

📥 Paso 2/4: Extrayendo datos del endpoint...
   📥 Consultando: https://gsn.maxapex.net/apex/savio/cotizaciones
   (con paginación automática)
   ✅ Total obtenidos: 4,850 registros

🔄 Paso 3/4: Transformando 4,850 registros...
   ✅ Transformados: 4,850 registros

💾 Paso 4/4: Sincronizando a Supabase...
   ✅ Sincronizados: 4,850 registros

======================================================================
✅ COMPLETADO
   📥 Extraídos: 4,850
   💾 Sincronizados: 4,850
   ⏱️  Duración: 12.3s
======================================================================

... (repite para los otros 7 controllers)
```

---

## ⚙️ GitHub Actions (Automático cada 6 horas)

### Configuración

**Workflow:** `.github/workflows/sync-erp-data.yml`

**Horario:** Cada 6 horas (00:00, 06:00, 12:00, 18:00 UTC)

### Paso 1: Configurar Secrets

En GitHub: `Settings → Secrets and variables → Actions`

| Secret | Valor | Ejemplo |
|--------|-------|---------|
| `ORACLE_APEX_BASE_URL` | URL de Oracle APEX | `https://gsn.maxapex.net/apex/savio` |
| `SUPABASE_URL` | URL de Supabase | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | API Key de Supabase | `eyJhbGci...` |

### Paso 2: Ejecutar

El workflow se ejecuta:
- **Automáticamente:** Cada 6 horas
- **Manualmente:** `Actions → Sincronización ERP → Run workflow`

---

## 🔒 Sistema de UPSERT (Sin Duplicados)

Cada registro tiene un `id` único usado como PRIMARY KEY:

```python
# Ejemplo: Cotizaciones
id = str(no_cotizacion)  # "24060001"

# Ejemplo: Proyectos Cliente
id = f"{no_cliente}_{no_proyecto}"  # "123_456"

# UPSERT automático
INSERT INTO cotizaciones (...) VALUES (...)
ON CONFLICT (id) DO UPDATE SET ...
```

**Resultado:**
- ✅ Si existe → Actualiza
- ✅ Si no existe → Inserta
- ❌ **No crea duplicados**

---

## 📈 Rendimiento

| Métrica | Valor |
|---------|-------|
| **Registros totales** | ~133,000 (sin v_log_cambios_etapa) |
| **Tiempo total** | ~2-3 minutos (sincronización incremental) |
| **Velocidad promedio** | ~740 registros/segundo |
| **Batch size** | 1,000 registros |
| **Timeout por request** | 60 segundos |
| **Endpoint más grande** | vidrios_produccion: 97,826 registros |
| **Sincronización incremental** | log_vidrios_produccion: reduce de 265K a ~15K |

---

## 📚 Documentación

### Documentación Principal

| Documento | Descripción |
|-----------|-------------|
| `README_NUEVO_SISTEMA.md` | 📖 Guía completa del usuario |
| `ARQUITECTURA.md` | 🏗️ Documentación técnica detallada |
| `MIGRACION_COMPLETADA.md` | 📦 Proceso de migración desde sistema anterior |

### Documentación Técnica

| Documento | Descripción |
|-----------|-------------|
| `VALIDACION_FINAL.md` | ✅ Validaciones de paginación y transformaciones |
| `SIN_VALIDACIONES.md` | 🔓 Por qué el sistema es permisivo |
| `PAGINACION_ORACLE_APEX.md` | 📄 Cómo funciona la paginación |
| `SCRIPT_SIMPLE.md` | 💡 Por qué el script es tan simple |

### Por Controller

Cada controller tiene su `README.md` en `controllers/{nombre}/README.md`:
- URL del endpoint
- Campos sincronizados
- Primary key
- Limitaciones (ej: no soporta filtros por fecha)
- Estrategia de sincronización

---

## 🆕 Cambios vs Sistema Anterior

| Aspecto | Antes | Ahora |
|---------|-------|-------|
| **Script** | `sync_all_endpoints.py` (337 líneas) | `sync_main.py` (100 líneas) |
| **Arquitectura** | Monolítico + JSON | Controllers autónomos |
| **Paginación** | ❌ No (solo 1,000 registros) | ✅ Automática (todos los registros) |
| **Validaciones** | ✅ Rechazaba incompletos | ❌ Permisivo (NULL si falta) |
| **Variables env** | 10+ | 3 |
| **CLI** | Con argparse | Sin CLI |
| **Transformaciones** | Archivo central | Una por controller |
| **Escalabilidad** | Baja | Alta |

**Ver:** `MIGRACION_COMPLETADA.md` para detalles completos

---

## 🛠️ Tecnologías

- **Python 3.11+**
- **Supabase** (PostgreSQL)
- **Oracle APEX REST API**
- **GitHub Actions**
- **Librerías:** `supabase-py`, `requests`, `python-dotenv`

---

## 🧪 Tests

### Tests de Validación de Datos (Sin Sincronizar)

Cada controller tiene un script `test_data.py` que extrae y transforma datos sin sincronizar a Supabase:

```bash
# Activar entorno virtual
source .venv/bin/activate

# Test de controllers individuales
python controllers/clientes/test_data.py
python controllers/cotizaciones/test_data.py
python controllers/detalle_cotizacion/test_data.py
python controllers/proyectos_cliente/test_data.py
python controllers/v_insumos/test_data.py
python controllers/vidrios_produccion/test_data.py

# Test con filtro de fecha (log_vidrios_produccion)
python controllers/log_vidrios_produccion/test_data.py 2026-01-01 2026-01-23

# Test limitado (v_log_cambios_etapa)
python controllers/v_log_cambios_etapa/test_data.py 10  # Solo 10 órdenes
```

Cada test:
- ✅ Extrae datos del endpoint Oracle APEX
- ✅ Transforma al formato Supabase
- ✅ Muestra estadísticas y muestra de datos
- ✅ Guarda resultado en JSON
- ❌ NO sincroniza a Supabase

### Tests de Arquitectura

```bash
# Verificar estructura
python test_arquitectura.py

# Verificar imports
python test_imports_manuales.py
```

Todos deben pasar ✅

---

## 📁 Estructura del Proyecto

```
senv-db-sync/
├── sync_main.py                    # ✅ Script principal
├── .env.example                    # ✅ Template de configuración
├── .env                            # 🔒 Variables de entorno (git-ignored)
├── controllers/                    # ✅ 8 controllers autónomos
│   ├── cotizaciones/
│   │   ├── cotizaciones.controller.py
│   │   ├── test_data.py           # 🧪 Test sin sincronizar
│   │   ├── components/
│   │   │   ├── get_data.py
│   │   │   ├── transform_data.py
│   │   │   └── synchronize.py
│   │   └── README.md
│   ├── clientes/
│   ├── proyectos_cliente/
│   ├── v_insumos/
│   ├── detalle_cotizacion/
│   ├── vidrios_produccion/
│   ├── log_vidrios_produccion/
│   └── v_log_cambios_etapa/
├── utils/                          # ✅ Utilidades compartidas
│   ├── http_client.py
│   ├── supabase_client.py
│   └── dates.py
├── .github/workflows/
│   └── sync-erp-data.yml          # ✅ GitHub Actions
├── requirements.txt
└── README.md                       # ← Este archivo
```

---

## 📞 Soporte

**Dataframe Consulting**

**Última actualización:** 23 de enero de 2026  
**Versión:** 2.0 (Sistema Nuevo - Controllers Autónomos)

---

## 🔗 Enlaces Útiles

- [Guía completa del usuario](README_NUEVO_SISTEMA.md)
- [Documentación técnica](ARQUITECTURA.md)
- [Proceso de migración](MIGRACION_COMPLETADA.md)
- [Validación del sistema](VALIDACION_FINAL.md)

---

## ⚡ Quick Start

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales reales

# 3. Ejecutar sincronización
python sync_main.py
```

✅ ¡Listo!
