"""Component: Transformación de datos para v_log_cambios_etapa."""

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


def transform_log_cambios_etapa(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforma registros de v_log_cambios_etapa.

    Cada fila es un evento histórico de cambio de etapa. El ID incluye fec_modif
    para preservar todos los eventos distintos como registros independientes
    (clon fiel del origen).

    ID Compuesto: {no_orden_produccion}_{dec_seq}_{vip_seq}_{no_etapa}_{fec_modif}

    Campos del API:
    - no_etapa, no_orden_produccion, no_cotizacion, dec_seq, vip_seq
    - no_insumo, no_insumo_final, usr_modif, fec_modif, status
    - no_etapa_actual, no_optimizacion, espesor, base, altura, m2
    - taladros_cot, canto_pulido, filo_muerto
    """
    no_orden = record.get('no_orden_produccion')
    dec_seq = record.get('dec_seq')
    vip_seq = record.get('vip_seq')
    no_etapa = record.get('no_etapa')
    fec_modif_raw = parse_oracle_date(record.get('fec_modif'))

    # ID incluye fec_modif para que cada evento histórico sea una fila única
    record_id = f"{no_orden}_{dec_seq}_{vip_seq}_{no_etapa}_{fec_modif_raw}"
    
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
        'fec_modif': fec_modif_raw,
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


def transform_all(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transforma todos los registros."""
    transformed = []
    errors = 0
    
    for record in records:
        try:
            transformed.append(transform_log_cambios_etapa(record))
        except Exception as e:
            errors += 1
            print(f"⚠️  Error transformando registro: {e}")
    
    if errors > 0:
        print(f"❌ Errores en transformación: {errors}")
    
    return transformed


def deduplicate_by_id(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Elimina filas exactamente repetidas (mismo ID).

    Como el ID incluye fec_modif, dos eventos distintos generan IDs distintos
    y ambos se conservan. Solo se elimina si el API devuelve el mismo registro
    más de una vez (duplicado real).
    """
    unique: Dict[str, Any] = {}
    for r in records:
        id_ = r.get('id')
        if not id_:
            continue
        unique.setdefault(id_, r)  # conserva la primera ocurrencia

    duplicates_removed = len(records) - len(unique)
    if duplicates_removed > 0:
        print(f"⚠️  Duplicados exactos removidos: {duplicates_removed}")

    return list(unique.values())
