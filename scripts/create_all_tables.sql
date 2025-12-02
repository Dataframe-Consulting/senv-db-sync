-- =====================================================
-- SCRIPT DE CREACIÓN DE TABLAS PARA SUPABASE
-- Sistema de sincronización ERP SAVIO → Supabase
-- =====================================================

-- IMPORTANTE: Este script elimina y recrea las tablas
-- Asegúrate de hacer un respaldo antes de ejecutarlo

-- =====================================================
-- 1. LOG_CAMBIOS_ETAPA
-- =====================================================

DROP TABLE IF EXISTS log_cambios_etapa CASCADE;

CREATE TABLE log_cambios_etapa (
    id TEXT PRIMARY KEY,  -- Formato: {no_orden}_{dec_seq}_{vip_seq}_{no_etapa}_{fec_modif}
    no_orden_produccion INTEGER,
    no_cotizacion INTEGER,
    dec_seq INTEGER,
    vip_seq INTEGER,
    no_etapa TEXT,
    no_insumo INTEGER,
    no_insumo_final INTEGER,
    usr_modif TEXT,
    fec_modif TIMESTAMP,
    status TEXT,
    no_etapa_actual INTEGER,
    no_optimizacion INTEGER,
    espesor NUMERIC,
    base INTEGER,
    altura INTEGER,
    m2 NUMERIC,
    taladros_cot INTEGER,
    canto_pulido NUMERIC,
    filo_muerto TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices para mejorar rendimiento
CREATE INDEX idx_log_cambios_etapa_orden ON log_cambios_etapa(no_orden_produccion);
CREATE INDEX idx_log_cambios_etapa_cotizacion ON log_cambios_etapa(no_cotizacion);
CREATE INDEX idx_log_cambios_etapa_fec ON log_cambios_etapa(fec_modif);
CREATE INDEX idx_log_cambios_etapa_status ON log_cambios_etapa(status);

-- =====================================================
-- 2. DETALLE_COTIZACION
-- =====================================================

DROP TABLE IF EXISTS detalle_cotizacion CASCADE;

CREATE TABLE detalle_cotizacion (
    id TEXT PRIMARY KEY,  -- Formato: {no_cotizacion}_{dec_seq}_{renglon}
    no_cotizacion INTEGER,
    dec_seq INTEGER,
    renglon INTEGER,
    clase_insumo TEXT,
    no_insumo INTEGER,
    base INTEGER,
    altura INTEGER,
    cantidad INTEGER,
    ref_ubicacion TEXT,
    no_sistema INTEGER,
    precio_unitario NUMERIC,
    dibujo TEXT,
    dibujo_filename TEXT,
    dibujo_mimetype TEXT,
    dibujo_last_update TIMESTAMP,
    dibujo_charset TEXT,
    precio_m2 NUMERIC,
    precio_pactado TEXT,
    forma_irregular TEXT,
    fec_crea TIMESTAMP,
    usr_crea TEXT,
    fec_modif TIMESTAMP,
    usr_modif TEXT,
    pagina_croquis INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_detalle_cotizacion_no_cot ON detalle_cotizacion(no_cotizacion);
CREATE INDEX idx_detalle_cotizacion_dec_seq ON detalle_cotizacion(dec_seq);
CREATE INDEX idx_detalle_cotizacion_fec_modif ON detalle_cotizacion(fec_modif);
CREATE INDEX idx_detalle_cotizacion_usr_modif ON detalle_cotizacion(usr_modif);

-- =====================================================
-- 3. VIDRIOS_PRODUCCION
-- =====================================================

DROP TABLE IF EXISTS vidrios_produccion CASCADE;

CREATE TABLE vidrios_produccion (
    id TEXT PRIMARY KEY,  -- Formato: {no_orden}_{no_cotizacion}_{dec_seq}_{vip_seq}
    no_orden_produccion INTEGER,
    no_cotizacion INTEGER,
    dec_seq INTEGER,
    vip_seq INTEGER,
    vip_seq_ens INTEGER,
    no_insumo INTEGER,
    clase TEXT,
    status TEXT,
    no_etapa INTEGER,
    hora_cambio_etapa TIMESTAMP,
    no_motivo_reproceso INTEGER,
    vip_seq_rep INTEGER,
    cve_ubicacion TEXT,
    fec_crea TIMESTAMP,
    usr_crea TEXT,
    fec_modif TIMESTAMP,
    usr_modif TEXT,
    base INTEGER,
    altura INTEGER,
    id_skyplanner TEXT,
    seq_clase INTEGER,
    foldoc_cxc INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_vidrios_produccion_orden ON vidrios_produccion(no_orden_produccion);
CREATE INDEX idx_vidrios_produccion_cotizacion ON vidrios_produccion(no_cotizacion);
CREATE INDEX idx_vidrios_produccion_status ON vidrios_produccion(status);
CREATE INDEX idx_vidrios_produccion_fec_modif ON vidrios_produccion(fec_modif);

-- =====================================================
-- 4. LOG_VIDRIOS_PRODUCCION
-- =====================================================

DROP TABLE IF EXISTS log_vidrios_produccion CASCADE;

CREATE TABLE log_vidrios_produccion (
    id TEXT PRIMARY KEY,  -- Formato: {no_orden}_{no_cotizacion}_{dec_seq}_{vip_seq}_{campo}_{fec_modif}
    no_orden_produccion INTEGER,
    no_cotizacion INTEGER,
    dec_seq INTEGER,
    vip_seq INTEGER,
    campo TEXT,
    valor_anterior TEXT,
    valor_nuevo TEXT,
    usr_modif TEXT,
    fec_modif TIMESTAMP,
    fec_modif_pre TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_log_vidrios_produccion_orden ON log_vidrios_produccion(no_orden_produccion);
CREATE INDEX idx_log_vidrios_produccion_cotizacion ON log_vidrios_produccion(no_cotizacion);
CREATE INDEX idx_log_vidrios_produccion_campo ON log_vidrios_produccion(campo);
CREATE INDEX idx_log_vidrios_produccion_fec ON log_vidrios_produccion(fec_modif);

-- =====================================================
-- VERIFICACIÓN
-- =====================================================

-- Verificar que las tablas se crearon correctamente
SELECT 
    tablename,
    (SELECT COUNT(*) FROM pg_indexes WHERE tablename = t.tablename) as num_indexes
FROM pg_tables t
WHERE schemaname = 'public'
    AND tablename IN ('log_cambios_etapa', 'detalle_cotizacion', 'vidrios_produccion', 'log_vidrios_produccion')
ORDER BY tablename;

-- Mostrar estructura de cada tabla
\d log_cambios_etapa
\d detalle_cotizacion
\d vidrios_produccion
\d log_vidrios_produccion
