"""Component: Transformación de datos para clientes."""

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


def transform_cliente(record: Dict[str, Any]) -> Dict[str, Any]:
    """Transforma un registro de cliente."""
    record_id = str(record.get('no_cliente'))
    
    return {
        'id': record_id,
        'no_cliente': record.get('no_cliente'),
        'razon_social': record.get('razon_social'),
        'rfc': record.get('rfc'),
        'e_mail': record.get('e_mail'),
        'nivel_precio': record.get('nivel_precio'),
        'telefonos': record.get('telefonos'),
        'notas': record.get('notas'),
        'notas_pago': record.get('notas_pago'),
        'atencion': record.get('atencion'),
        'limite_credito': record.get('limite_credito'),
        'dias_credito': record.get('dias_credito'),
        'fec_crea': parse_oracle_date(record.get('fec_crea')),
        'usr_crea': record.get('usr_crea'),
        'fec_modif': parse_oracle_date(record.get('fec_modif')),
        'usr_modif': record.get('usr_modif'),
        'siglas': record.get('siglas'),
        'no_emp_vendedor': record.get('no_emp_vendedor'),
        'regimen_fiscal': record.get('regimen_fiscal'),
        'cp': record.get('cp'),
        'direccion': record.get('direccion'),
        'e_mail_compras': record.get('e_mail_compras'),
        'cve_uso_cfdi': record.get('cve_uso_cfdi')
    }


def transform_all(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma todos los registros."""
    transformed = []
    errors = 0
    
    for record in records:
        try:
            transformed.append(transform_cliente(record))
        except Exception as e:
            errors += 1
            print(f"⚠️  Error transformando cliente {record.get('no_cliente')}: {e}")
    
    if errors > 0:
        print(f"❌ Errores en transformación: {errors}")
    
    return transformed


def deduplicate_by_id(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplica por ID."""
    unique = {r['id']: r for r in records if r.get('id')}
    
    if len(records) > len(unique):
        print(f"⚠️  Duplicados removidos: {len(records) - len(unique)}")
    
    return list(unique.values())
