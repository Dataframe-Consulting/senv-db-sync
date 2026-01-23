"""Component: Transformación de datos para proyectos_cliente."""

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


def transform_proyectos_cliente(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma registros de proyectos_cliente.
    
    URL Pattern: /proyectos_cliente/{no_cliente},{no_proyecto}
    ID Compuesto: {no_cliente}_{no_proyecto}
    
    Campos del API:
    - no_cliente, no_proyecto, nom_proyecto, num_proy_cliente
    - txt_proy_cliente, importe_anticipo, pct_anticipo
    - fec_crea, usr_crea, fec_modif, usr_modif, id_skyplanner
    """
    no_cliente = record.get('no_cliente')
    no_proyecto = record.get('no_proyecto')
    record_id = f"{no_cliente}_{no_proyecto}"
    
    return {
        'id': record_id,
        'no_cliente': no_cliente,
        'no_proyecto': no_proyecto,
        'nom_proyecto': record.get('nom_proyecto'),
        'num_proy_cliente': record.get('num_proy_cliente'),
        'txt_proy_cliente': record.get('txt_proy_cliente'),
        'importe_anticipo': record.get('importe_anticipo'),
        'pct_anticipo': record.get('pct_anticipo'),
        'fec_crea': parse_oracle_date(record.get('fec_crea')),
        'usr_crea': record.get('usr_crea'),
        'fec_modif': parse_oracle_date(record.get('fec_modif')),
        'usr_modif': record.get('usr_modif'),
        'id_skyplanner': record.get('id_skyplanner')
    }


def transform_all(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma todos los registros."""
    transformed = []
    errors = 0
    
    for record in records:
        try:
            transformed.append(transform_proyectos_cliente(record))
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
