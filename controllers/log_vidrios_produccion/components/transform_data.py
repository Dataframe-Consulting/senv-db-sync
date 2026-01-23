"""Component: Transformación de datos para log_vidrios_produccion."""

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


def transform_all(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma todos los registros."""
    transformed = []
    errors = 0
    
    for record in records:
        try:
            transformed.append(transform_log_vidrios_produccion(record))
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
