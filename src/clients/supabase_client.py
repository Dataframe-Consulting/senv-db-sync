"""
Cliente para Supabase.
"""

from typing import List, Dict, Any
from supabase import create_client, Client
from ..config.settings import SupabaseConfig


class SupabaseClient:
    """Cliente para insertar datos en Supabase."""
    
    def __init__(self, config: SupabaseConfig):
        self.config = config
        self.client: Client = create_client(config.url, config.key)
    
    def batch_upsert(
        self,
        records: List[Dict[str, Any]],
        batch_size: int = 100,
        conflict_column: str = 'id'
    ) -> int:
        """
        Inserta o actualiza registros por lotes (UPSERT).
        
        Args:
            records: Lista de registros a insertar
            batch_size: Tamaño del batch
            conflict_column: Columna para resolver conflictos
            
        Returns:
            Número de registros insertados/actualizados
        """
        if not records:
            return 0
        
        total_inserted = 0
        
        # Procesar en batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            try:
                # UPSERT: inserta o actualiza si ya existe
                response = self.client.table(self.config.table_name).upsert(
                    batch,
                    on_conflict=conflict_column
                ).execute()
                
                # Contar registros afectados
                if hasattr(response, 'data') and response.data:
                    total_inserted += len(response.data)
                else:
                    total_inserted += len(batch)
                
            except Exception as e:
                print(f"❌ Error al insertar batch {i//batch_size + 1}: {e}")
                # Continuar con el siguiente batch
                continue
        
        return total_inserted
    
    def insert_batch(self, records: List[Dict[str, Any]]) -> int:
        """
        Inserta múltiples registros (sin UPSERT).
        
        Args:
            records: Lista de registros
            
        Returns:
            Número de registros insertados
        """
        if not records:
            return 0
        
        try:
            response = self.client.table(self.config.table_name).insert(records).execute()
            return len(response.data) if hasattr(response, 'data') else len(records)
        except Exception as e:
            print(f"❌ Error al insertar: {e}")
            return 0
    
    def count_records(self) -> int:
        """
        Cuenta el total de registros en la tabla.
        
        Returns:
            Número de registros
        """
        try:
            response = self.client.table(self.config.table_name).select('id', count='exact').execute()
            return response.count if hasattr(response, 'count') else 0
        except Exception as e:
            print(f"❌ Error al contar registros: {e}")
            return 0
