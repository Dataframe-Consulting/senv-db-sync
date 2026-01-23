"""Component: Transformación de datos para detalle_cotizacion."""

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


def transform_all(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma todos los registros."""
    transformed = []
    errors = 0
    
    for record in records:
        try:
            transformed.append(transform_detalle_cotizacion(record))
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
