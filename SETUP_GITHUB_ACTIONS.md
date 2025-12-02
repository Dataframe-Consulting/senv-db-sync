# 🚀 GUÍA DE CONFIGURACIÓN RÁPIDA - GitHub Actions

## ✅ PASOS PARA ACTIVAR LA SINCRONIZACIÓN AUTOMÁTICA

### 1️⃣ Crear las Tablas en Supabase (PRIMERO)

1. Abre tu proyecto en Supabase: https://supabase.com/dashboard
2. Ve a: **SQL Editor**
3. Copia y pega el contenido completo de: `scripts/create_all_tables.sql`
4. Haz clic en **Run** o presiona `Ctrl/Cmd + Enter`
5. Verifica que se crearon las 4 tablas:
   - `log_cambios_etapa`
   - `detalle_cotizacion`
   - `vidrios_produccion`
   - `log_vidrios_produccion`

### 2️⃣ Configurar Environment en GitHub

1. Ve a tu repositorio: https://github.com/Dataframe-Consulting/senv-db-sync
2. Haz clic en: **Settings** (arriba)
3. En el menú lateral: **Environments**
4. Haz clic en: **New environment**
5. Nombre: `production`
6. Haz clic en: **Configure environment**

### 3️⃣ Agregar los Secrets

En la sección **Environment secrets**, haz clic en **Add environment secret** para cada uno:

#### Secret 1: ORACLE_APEX_BASE_URL
- **Name**: `ORACLE_APEX_BASE_URL`
- **Value**: `https://gsn.maxapex.net/ords/savio`

#### Secret 2: ORACLE_APEX_USERNAME
- **Name**: `ORACLE_APEX_USERNAME`
- **Value**: (tu usuario de Oracle APEX)

#### Secret 3: ORACLE_APEX_PASSWORD
- **Name**: `ORACLE_APEX_PASSWORD`
- **Value**: (tu contraseña de Oracle APEX)

#### Secret 4: SUPABASE_URL
- **Name**: `SUPABASE_URL`
- **Value**: (tu URL de Supabase, ejemplo: `https://xxxxx.supabase.co`)

#### Secret 5: SUPABASE_KEY
- **Name**: `SUPABASE_KEY`
- **Value**: (tu API Key de Supabase - usar `service_role` key para mejor rendimiento)

#### Secret 6: SUPABASE_DB_PASSWORD
- **Name**: `SUPABASE_DB_PASSWORD`
- **Value**: (contraseña de tu base de datos Supabase)

### 4️⃣ Ejecutar la Primera Sincronización (MANUAL)

1. Ve a: **Actions** (pestaña superior del repo)
2. En el menú lateral: **Sincronización ERP APEX → Supabase (cada hora)**
3. Haz clic en: **Run workflow** (botón derecho)
4. Deja el branch en `main`
5. Haz clic en: **Run workflow** (botón verde)
6. Espera a que termine (puede tomar 2-3 horas en la primera sincronización)

### 5️⃣ Verificar la Sincronización

Durante la ejecución, puedes ver el progreso:
1. Haz clic en el workflow que está corriendo
2. Haz clic en el job **sync-data**
3. Verás los logs en tiempo real con estadísticas:
   - 📥 Registros extraídos
   - 💾 Registros insertados
   - ⚡ Velocidad (registros/segundo)
   - ✅/❌ Estado de cada endpoint

### 6️⃣ Verificar los Datos en Supabase

1. Ve a Supabase: **Table Editor**
2. Verifica que cada tabla tenga datos:
   ```sql
   SELECT COUNT(*) FROM log_cambios_etapa;
   SELECT COUNT(*) FROM detalle_cotizacion;
   SELECT COUNT(*) FROM vidrios_produccion;
   SELECT COUNT(*) FROM log_vidrios_produccion;
   ```

---

## 🎯 RESULTADO ESPERADO

✅ **Sincronización automática cada hora**: Los datos se actualizarán cada 60 minutos sin tu intervención

✅ **Sin duplicados**: El sistema usa UPSERT con IDs únicos, los registros existentes se actualizan

✅ **4 endpoints sincronizados**: Todos los endpoints se procesan en una sola ejecución

✅ **Logs detallados**: Puedes revisar cada sincronización en la pestaña Actions

---

## 📊 MONITOREO

### Ver Logs de Sincronizaciones Pasadas
1. Ve a: **Actions**
2. Selecciona cualquier ejecución pasada
3. Descarga los logs si necesitas analizarlos

### Configurar Notificaciones
- GitHub te enviará un email si alguna sincronización falla
- Puedes configurar notificaciones adicionales en **Settings → Notifications**

---

## 🔧 TROUBLESHOOTING

### ❌ Error: "Missing required variables"
- Verifica que todos los 6 secrets estén configurados correctamente
- Asegúrate de que el environment se llame exactamente `production`

### ❌ Error: "Authentication failed"
- Verifica las credenciales de Oracle APEX
- Verifica que la URL base sea correcta

### ❌ Error: "Supabase connection failed"
- Verifica que la SUPABASE_URL sea correcta (debe terminar en `.supabase.co`)
- Verifica que estés usando la `service_role` key (no la `anon` key)

### ⚠️ La sincronización toma mucho tiempo
- Es normal en la primera ejecución (2-3 horas)
- Las siguientes sincronizaciones serán más rápidas (solo datos nuevos)

---

## 📞 SOPORTE

**Dataframe Consulting**  
Leonardo Toledo  
Diciembre 2025

---

## 🎉 ¡LISTO!

Una vez completados estos pasos:
- ✅ Los datos se sincronizarán automáticamente cada hora
- ✅ No hay riesgo de duplicados
- ✅ Los logs te permitirán monitorear el proceso
- ✅ No necesitas hacer nada más, el sistema funciona solo

**¡Disfruta de tu sincronización automática!** 🚀
