"""Component: Transformación de datos para vidrios_produccion."""

from typing import Dict, Any, List
from datetime import datetime


def parse_oracle_date(date_str: str | None) -> str | None:
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


def transform_all(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma todos los registros."""
    transformed = []
    errors = 0
    
    for record in records:
        try:
            transformed.append(transform_vidrios_produccion(record))
        except Exception as e:
            errors += 1
            print(f"⚠️  Error transformando registro: {e}")
    
    if errors > 0:
        print(f"❌ Errores en transformación: {errors}")
    
    return transformed


def deduplicate_by_id(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplica por ID."""
    unique = {r['id']: r for r in records if r.get('id')}
    
    if len(records) > len(unique):
        print(f"⚠️  Duplicados removidos: {len(records) - len(unique)}")
    
    return list(unique.values())
