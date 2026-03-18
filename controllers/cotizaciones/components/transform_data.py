"""
Component: Transformación de datos para cotizaciones.
Convierte del formato Oracle APEX al formato Supabase.
"""

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


def transform_cotizacion(
    record: Dict[str, Any],
    fechas_entrega: Dict[int, str] | None = None
) -> Dict[str, Any]:
    """
    Transforma un registro de cotización de Oracle APEX a formato Supabase.

    Args:
        record: Registro en formato Oracle APEX
        fechas_entrega: Lookup {no_cotizacion: fecha_entrega_programada} obtenido
                        de v_status_pedidos. Solo se incluye en el payload cuando
                        existe una fecha para ese no_cotizacion.

    Returns:
        Registro transformado para Supabase
    """
    no_cotizacion = record.get('no_cotizacion')
    record_id = str(no_cotizacion)

    transformed = {
        # Primary Key
        'id': record_id,

        # Datos principales
        'no_cotizacion': no_cotizacion,
        'no_contacto': record.get('no_contacto'),
        'fecha': parse_oracle_date(record.get('fecha')),
        'no_cliente': record.get('no_cliente'),
        'status': record.get('status'),
        'no_proyecto': record.get('no_proyecto'),

        # Detalles comerciales
        'comentarios': record.get('comentarios'),
        'solo_maquila': record.get('solo_maquila'),
        'pct_descuento': record.get('pct_descuento'),
        'no_emp_vendedor': record.get('no_emp_vendedor'),

        # Fechas y referencias
        'fec_valorizacion': parse_oracle_date(record.get('fec_valorizacion')),
        'comprobante': record.get('comprobante'),
        'moneda': record.get('moneda'),
        'referencia': record.get('referencia'),
        'no_orden_compra': record.get('no_orden_compra'),

        # Auditoría
        'fec_crea': parse_oracle_date(record.get('fec_crea')),
        'usr_crea': record.get('usr_crea'),
        'fec_modif': parse_oracle_date(record.get('fec_modif')),
        'usr_modif': record.get('usr_modif'),
    }

    # Solo incluir fecha_entrega_programada si existe en el lookup,
    # para no sobreescribir con NULL cotizaciones sin pedido activo.
    if fechas_entrega and no_cotizacion in fechas_entrega:
        transformed['fecha_entrega_programada'] = fechas_entrega[no_cotizacion]

    return transformed


def build_fechas_entrega_lookup(status_records: List[Dict[str, Any]]) -> Dict[int, str]:
    """
    Construye un dict {no_cotizacion: fecha_entrega_programada} a partir de los
    registros crudos de v_status_pedidos. Solo incluye entradas con fec_prog_entrega
    no nulo. Si hay varios pedidos del mismo no_cotizacion, se queda con el primero.
    """
    lookup: Dict[int, str] = {}
    for r in status_records:
        no_cot = r.get('no_cotizacion')
        fec = r.get('fec_prog_entrega')
        if no_cot and fec and no_cot not in lookup:
            lookup[no_cot] = parse_oracle_date(fec)
    return lookup


def transform_all(
    records: List[Dict[str, Any]],
    fechas_entrega: Dict[int, str] | None = None
) -> List[Dict[str, Any]]:
    """
    Transforma una lista de registros.

    Args:
        records: Lista de registros en formato Oracle APEX
        fechas_entrega: Lookup opcional {no_cotizacion: fecha_entrega_programada}

    Returns:
        Lista de registros transformados
    """
    transformed = []
    errors = 0

    for record in records:
        try:
            transformed_record = transform_cotizacion(record, fechas_entrega)
            transformed.append(transformed_record)
        except Exception as e:
            errors += 1
            print(f"⚠️  Error al transformar registro {record.get('no_cotizacion')}: {e}")
    
    if errors > 0:
        print(f"❌ Total de errores en transformación: {errors}")
    
    return transformed


def deduplicate_by_id(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplica registros por ID, manteniendo el último.
    
    Args:
        records: Lista de registros (potencialmente con duplicados)
        
    Returns:
        Lista sin duplicados
    """
    unique = {}
    
    for record in records:
        record_id = record.get('id')
        if record_id:
            unique[record_id] = record
    
    original_count = len(records)
    final_count = len(unique)
    
    if original_count > final_count:
        print(f"⚠️  Duplicados removidos: {original_count - final_count}")
    
    return list(unique.values())
