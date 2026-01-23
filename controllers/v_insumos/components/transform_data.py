"""Component: Transformación de datos para v_insumos."""

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


def transform_v_insumos(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma registros de v_insumos.
    
    URL Pattern: /v_insumos/{no_insumo}
    ID: {no_insumo}
    
    Campos del API:
    - no_insumo, clave_estandar, descripcion, nom_largo
    - tipo_insumo, cve_linea, cve_generica, cve_tipo_vidrio
    - no_espesor, no_medida, no_acabado, no_longitud
    - cve_unidad, precio_mxn, precio_usd, precio_eur
    - costo_promedio, no_insumo_gsns, espesor, vigente
    - id_skyplanner, tiempo_pre_proceso, tiempo_proceso, tiempo_post_proceso
    """
    record_id = str(record.get('no_insumo'))
    
    return {
        'id': record_id,
        'no_insumo': record.get('no_insumo'),
        'clave_estandar': record.get('clave_estandar'),
        'descripcion': record.get('descripcion'),
        'nom_largo': record.get('nom_largo'),
        'tipo_insumo': record.get('tipo_insumo'),
        'cve_linea': record.get('cve_linea'),
        'cve_generica': record.get('cve_generica'),
        'cve_tipo_vidrio': record.get('cve_tipo_vidrio'),
        'no_espesor': record.get('no_espesor'),
        'no_medida': record.get('no_medida'),
        'no_acabado': record.get('no_acabado'),
        'no_longitud': record.get('no_longitud'),
        'cve_unidad': record.get('cve_unidad'),
        'precio_mxn': record.get('precio_mxn'),
        'precio_usd': record.get('precio_usd'),
        'precio_eur': record.get('precio_eur'),
        'costo_promedio': record.get('costo_promedio'),
        'no_insumo_gsns': record.get('no_insumo_gsns'),
        'espesor': record.get('espesor'),
        'vigente': record.get('vigente'),
        'id_skyplanner': record.get('id_skyplanner'),
        'tiempo_pre_proceso': record.get('tiempo_pre_proceso'),
        'tiempo_proceso': record.get('tiempo_proceso'),
        'tiempo_post_proceso': record.get('tiempo_post_proceso')
    }


def transform_all(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma todos los registros."""
    transformed = []
    errors = 0
    
    for record in records:
        try:
            transformed.append(transform_v_insumos(record))
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
