"""
Cliente Supabase para operaciones CRUD.
Utilidad transversal sin conocimiento de dominio.
"""

import os
from typing import List, Dict, Any, Optional
from supabase import create_client, Client


# Cliente global (singleton pattern funcional)
_supabase_client = None


def get_supabase_client() -> Client:
    """
    Retorna cliente Supabase (singleton).
    Lee credenciales de variables de entorno.
    
    Returns:
        Cliente Supabase configurado
        
    Raises:
        ValueError: Si faltan variables de entorno
    """
    global _supabase_client
    
    if _supabase_client is None:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError(
                "Faltan variables de entorno: SUPABASE_URL y/o SUPABASE_KEY"
            )
        
        _supabase_client = create_client(url, key)
    
    return _supabase_client


def batch_upsert(
    table_name: str,
    records: List[Dict[str, Any]],
    conflict_column: str = 'id',
    batch_size: int = 1000,
    verbose: bool = True
) -> int:
    """
    Inserta/actualiza registros en lotes (UPSERT).
    
    Args:
        table_name: Nombre de la tabla en Supabase
        records: Lista de registros a insertar
        conflict_column: Columna para detectar conflictos (default: 'id')
        batch_size: Tamaño de cada lote
        verbose: Si mostrar progreso
        
    Returns:
        Número total de registros procesados
        
    Raises:
        Exception: Si hay error en la inserción
    """
    if not records:
        return 0
    
    client = get_supabase_client()
    total_inserted = 0
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        
        try:
            # UPSERT: on_conflict especifica la columna de conflicto
            response = (
                client.table(table_name)
                .upsert(batch, on_conflict=conflict_column)
                .execute()
            )
            
            total_inserted += len(batch)
            
            if verbose and len(records) > batch_size:
                print(f"   💾 Insertados: {total_inserted:,}/{len(records):,}")
        
        except Exception as e:
            # Mostrar más detalles del error para debugging
            print(f"❌ Error en batch {i//batch_size + 1}: {e}")
            if hasattr(e, 'message'):
                print(f"   Detalles: {e.message}")
            raise
    
    return total_inserted


def get_max_date(
    table_name: str,
    date_column: str = 'fec_modif'
) -> Optional[str]:
    """
    Obtiene la fecha máxima de una columna (útil para sync incremental).
    
    Args:
        table_name: Nombre de la tabla
        date_column: Nombre de la columna de fecha
        
    Returns:
        Fecha máxima en formato ISO string o None si la tabla está vacía
    """
    try:
        client = get_supabase_client()
        
        response = (
            client.table(table_name)
            .select(date_column)
            .order(date_column, desc=True)
            .limit(1)
            .execute()
        )
        
        if response.data and len(response.data) > 0:
            return response.data[0].get(date_column)
        
        return None
    
    except Exception as e:
        print(f"⚠️  Error al obtener max_date de {table_name}.{date_column}: {e}")
        return None


def count_records(table_name: str) -> int:
    """
    Cuenta el número de registros en una tabla.
    
    Args:
        table_name: Nombre de la tabla
        
    Returns:
        Número de registros
    """
    try:
        client = get_supabase_client()
        
        response = (
            client.table(table_name)
            .select('*', count='exact')
            .limit(1)
            .execute()
        )
        
        return response.count if hasattr(response, 'count') else 0
    
    except Exception as e:
        print(f"⚠️  Error al contar registros de {table_name}: {e}")
        return 0


def truncate_table(table_name: str, confirm: bool = False) -> bool:
    """
    Elimina todos los registros de una tabla (usar con cuidado).
    
    Args:
        table_name: Nombre de la tabla
        confirm: Flag de confirmación (debe ser True para ejecutar)
        
    Returns:
        True si se ejecutó correctamente
    """
    if not confirm:
        print("⚠️  truncate_table requiere confirm=True para ejecutar")
        return False
    
    try:
        client = get_supabase_client()
        
        # Nota: Supabase no tiene TRUNCATE directo, usamos DELETE sin condiciones
        # Esto puede ser lento para tablas grandes
        response = (
            client.table(table_name)
            .delete()
            .neq('id', '')  # Condición que matchea todo
            .execute()
        )
        
        print(f"✅ Tabla {table_name} truncada")
        return True
    
    except Exception as e:
        print(f"❌ Error al truncar tabla {table_name}: {e}")
        return False
