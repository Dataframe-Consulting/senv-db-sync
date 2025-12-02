"""
Transformaciones para los 4 endpoints de SAVIO.
Cada transformación genera un ID único y convierte los campos al formato correcto.
"""

from datetime import datetime
from typing import Dict, Any, Optional


def parse_oracle_date(date_str: Optional[str]) -> Optional[str]:
    """
    Convierte fechas de Oracle APEX (ISO 8601) a formato PostgreSQL.
    Ejemplo: "2024-05-30T20:56:43Z" -> "2024-05-30 20:56:43"
    """
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError):
        return None


# ======================================================================
# 1. V_LOG_CAMBIOS_ETAPA (PRIORITARIO)
# ======================================================================

def transform_log_cambios_etapa(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma registros de v_log_cambios_etapa.
    
    URL Pattern: /v_log_cambios_etapa/{no_orden},{dec_seq},{vip_seq},{no_etapa}
    ID Compuesto: {no_orden_produccion}_{dec_seq}_{vip_seq}_{no_etapa}
    
    Campos del API:
    - no_etapa, no_orden_produccion, no_cotizacion, dec_seq, vip_seq
    - no_insumo, no_insumo_final, usr_modif, fec_modif, status
    - no_etapa_actual, no_optimizacion, espesor, base, altura, m2
    - taladros_cot, canto_pulido, filo_muerto
    """
    # Generar ID único compuesto basado en la URL del endpoint (SIN fecha para evitar duplicados)
    no_orden = record.get('no_orden_produccion')
    dec_seq = record.get('dec_seq')
    vip_seq = record.get('vip_seq')
    no_etapa = record.get('no_etapa')
    
    # Crear ID único que previene duplicados (sin fec_modif)
    record_id = f"{no_orden}_{dec_seq}_{vip_seq}_{no_etapa}"
    
    return {
        'id': record_id,
        'no_orden_produccion': no_orden,
        'no_cotizacion': record.get('no_cotizacion'),
        'dec_seq': dec_seq,
        'vip_seq': vip_seq,
        'no_etapa': no_etapa,
        'no_insumo': record.get('no_insumo'),
        'no_insumo_final': record.get('no_insumo_final'),
        'usr_modif': record.get('usr_modif'),
        'fec_modif': parse_oracle_date(record.get('fec_modif')),
        'status': record.get('status'),
        'no_etapa_actual': record.get('no_etapa_actual'),
        'no_optimizacion': record.get('no_optimizacion'),
        'espesor': record.get('espesor'),
        'base': record.get('base'),
        'altura': record.get('altura'),
        'm2': record.get('m2'),
        'taladros_cot': record.get('taladros_cot'),
        'canto_pulido': record.get('canto_pulido'),
        'filo_muerto': record.get('filo_muerto')
    }


# ======================================================================
# 2. LOG_VIDRIOS_PRODUCCION
# ======================================================================

def transform_log_vidrios_produccion(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma registros de log_vidrios_produccion.
    
    URL Pattern: /log_vidrios_produccion/{no_orden},{no_cotizacion},{dec_seq},{vip_seq},{campo},{fec_modif}
    ID Compuesto: {no_orden_produccion}_{no_cotizacion}_{dec_seq}_{vip_seq}_{campo}_{fec_modif}
    
    NOTA: Este endpoint SÍ incluye fec_modif en el ID porque es un LOG de cambios,
    cada cambio con diferente fecha es un registro diferente (no es duplicado).
    
    Campos del API:
    - no_orden_produccion, no_cotizacion, dec_seq, vip_seq
    - campo, fec_modif, valor_anterior, valor_nuevo
    - usr_modif, fec_modif_pre
    """
    no_orden = record.get('no_orden_produccion')
    no_cotizacion = record.get('no_cotizacion')
    dec_seq = record.get('dec_seq')
    vip_seq = record.get('vip_seq')
    campo = record.get('campo', '')
    fec_modif = record.get('fec_modif', '')
    
    # ID basado en la URL del endpoint (incluye fecha porque es un log de cambios)
    record_id = f"{no_orden}_{no_cotizacion}_{dec_seq}_{vip_seq}_{campo}_{fec_modif}"
    
    return {
        'id': record_id,
        'no_orden_produccion': no_orden,
        'no_cotizacion': no_cotizacion,
        'dec_seq': dec_seq,
        'vip_seq': vip_seq,
        'campo': record.get('campo'),
        'valor_anterior': record.get('valor_anterior'),
        'valor_nuevo': record.get('valor_nuevo'),
        'usr_modif': record.get('usr_modif'),
        'fec_modif': parse_oracle_date(record.get('fec_modif')),
        'fec_modif_pre': parse_oracle_date(record.get('fec_modif_pre'))
    }


# ======================================================================
# 3. DETALLE_COTIZACION
# ======================================================================

def transform_detalle_cotizacion(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma registros de detalle_cotizacion.
    
    URL Pattern: /detalle_cotizacion/{no_cotizacion},{dec_seq}
    ID Compuesto: {no_cotizacion}_{dec_seq}_{renglon}
    
    Campos del API:
    - no_cotizacion, dec_seq, renglon, clase_insumo, no_insumo
    - base, altura, cantidad, ref_ubicacion, no_sistema
    - precio_unitario, dibujo*, precio_m2, precio_pactado, forma_irregular
    - fec_crea, usr_crea, fec_modif, usr_modif, pagina_croquis
    """
    no_cot = record.get('no_cotizacion')
    dec_seq = record.get('dec_seq')
    renglon = record.get('renglon')
    
    # ID basado en URL del endpoint
    record_id = f"{no_cot}_{dec_seq}_{renglon}"
    
    return {
        'id': record_id,
        'no_cotizacion': no_cot,
        'dec_seq': dec_seq,
        'renglon': renglon,
        'clase_insumo': record.get('clase_insumo'),
        'no_insumo': record.get('no_insumo'),
        'base': record.get('base'),
        'altura': record.get('altura'),
        'cantidad': record.get('cantidad'),
        'ref_ubicacion': record.get('ref_ubicacion'),
        'no_sistema': record.get('no_sistema'),
        'precio_unitario': record.get('precio_unitario'),
        'dibujo': record.get('dibujo'),
        'dibujo_filename': record.get('dibujo_filename'),
        'dibujo_mimetype': record.get('dibujo_mimetype'),
        'dibujo_last_update': parse_oracle_date(record.get('dibujo_last_update')),
        'dibujo_charset': record.get('dibujo_charset'),
        'precio_m2': record.get('precio_m2'),
        'precio_pactado': record.get('precio_pactado'),
        'forma_irregular': record.get('forma_irregular'),
        'fec_crea': parse_oracle_date(record.get('fec_crea')),
        'usr_crea': record.get('usr_crea'),
        'fec_modif': parse_oracle_date(record.get('fec_modif')),
        'usr_modif': record.get('usr_modif'),
        'pagina_croquis': record.get('pagina_croquis')
    }


# ======================================================================
# 4. VIDRIOS_PRODUCCION
# ======================================================================

def transform_vidrios_produccion(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma registros de vidrios_produccion.
    
    URL Pattern: /vidrios_produccion/{no_orden},{no_cotizacion},{dec_seq},{vip_seq}
    ID Compuesto: {no_orden_produccion}_{no_cotizacion}_{dec_seq}_{vip_seq}
    
    Campos del API:
    - no_orden_produccion, no_cotizacion, dec_seq, vip_seq
    - vip_seq_ens, no_insumo, clase, status, no_etapa
    - hora_cambio_etapa, no_motivo_reproceso, vip_seq_rep, cve_ubicacion
    - fec_crea, usr_crea, fec_modif, usr_modif
    - base, altura, id_skyplanner, seq_clase, foldoc_cxc
    """
    no_orden = record.get('no_orden_produccion')
    no_cotizacion = record.get('no_cotizacion')
    dec_seq = record.get('dec_seq')
    vip_seq = record.get('vip_seq')
    
    # ID basado en URL del endpoint
    record_id = f"{no_orden}_{no_cotizacion}_{dec_seq}_{vip_seq}"
    
    return {
        'id': record_id,
        'no_orden_produccion': no_orden,
        'no_cotizacion': no_cotizacion,
        'dec_seq': dec_seq,
        'vip_seq': vip_seq,
        'vip_seq_ens': record.get('vip_seq_ens'),
        'no_insumo': record.get('no_insumo'),
        'clase': record.get('clase'),
        'status': record.get('status'),
        'no_etapa': record.get('no_etapa'),
        'hora_cambio_etapa': parse_oracle_date(record.get('hora_cambio_etapa')),
        'no_motivo_reproceso': record.get('no_motivo_reproceso'),
        'vip_seq_rep': record.get('vip_seq_rep'),
        'cve_ubicacion': record.get('cve_ubicacion'),
        'fec_crea': parse_oracle_date(record.get('fec_crea')),
        'usr_crea': record.get('usr_crea'),
        'fec_modif': parse_oracle_date(record.get('fec_modif')),
        'usr_modif': record.get('usr_modif'),
        'base': record.get('base'),
        'altura': record.get('altura'),
        'id_skyplanner': record.get('id_skyplanner'),
        'seq_clase': record.get('seq_clase'),
        'foldoc_cxc': record.get('foldoc_cxc')
    }


# ======================================================================
# DICCIONARIO DE TRANSFORMACIONES
# ======================================================================

TRANSFORMATIONS = {
    'v_log_cambios_etapa': transform_log_cambios_etapa,
    'log_vidrios_produccion': transform_log_vidrios_produccion,
    'detalle_cotizacion': transform_detalle_cotizacion,
    'vidrios_produccion': transform_vidrios_produccion
}

TABLES = {
    'v_log_cambios_etapa': 'log_cambios_etapa',
    'log_vidrios_produccion': 'log_vidrios_produccion',
    'detalle_cotizacion': 'detalle_cotizacion',
    'vidrios_produccion': 'vidrios_produccion'
}
