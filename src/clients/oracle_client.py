"""
Cliente para Oracle APEX REST Data Services.
"""

import requests
import time
from typing import List, Dict, Any, Tuple
from ..config.settings import OracleApexConfig, SyncConfig


class OracleApexClient:
    """Cliente para extraer datos de Oracle APEX."""
    
    def __init__(self, config: OracleApexConfig, sync_config: SyncConfig):
        self.config = config
        self.sync_config = sync_config
        self.session = requests.Session()
        self.session.auth = (config.username, config.password)
        self.session.headers.update({
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def _fetch_batch(self, offset: int = 0, since_date: str = None) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Obtiene un batch de registros desde Oracle APEX.

        Args:
            offset: Desplazamiento para paginación
            since_date: Fecha ISO para filtrar solo registros modificados después de esta fecha

        Returns:
            Tupla (registros, éxito)
        """
        url = f"{self.config.base_url}/{self.config.endpoint}"
        params = {
            'offset': offset,
            'limit': self.sync_config.batch_size
        }

        # Filtrado incremental por fecha de modificación
        if since_date:
            # Oracle APEX REST usa formato q={"fec_modif":{"$gte":"2025-12-30T00:00:00Z"}}
            params['q'] = f'{{"fec_modif":{{"$gte":"{since_date}"}}}}'
        
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.get(
                    url,
                    params=params,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    return items, True
                
                elif response.status_code == 404:
                    # No hay más registros
                    return [], True
                
                else:
                    print(f"⚠️  Status {response.status_code} en intento {attempt + 1}/{self.config.max_retries}")
                    
            except requests.exceptions.Timeout:
                print(f"⏱️  Timeout en intento {attempt + 1}/{self.config.max_retries}")
            except requests.exceptions.RequestException as e:
                print(f"❌ Error de red en intento {attempt + 1}/{self.config.max_retries}: {e}")
            
            # Esperar antes de reintentar
            if attempt < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay)
        
        return [], False
    
    def fetch_all(self, since_date: str = None) -> List[Dict[str, Any]]:
        """
        Obtiene todos los registros del endpoint.

        Args:
            since_date: Fecha ISO para sincronización incremental (opcional)

        Returns:
            Lista con todos los registros
        """
        all_records = []
        offset = 0

        if since_date:
            print(f"🔄 Sincronización incremental desde: {since_date}")
        else:
            print(f"📥 Sincronización completa (todos los registros)")

        while True:
            records, success = self._fetch_batch(offset, since_date)

            if not success:
                print(f"⚠️  Error al obtener batch en offset {offset}")
                break

            if not records:
                break

            all_records.extend(records)
            offset += self.sync_config.batch_size

            print(f"📥 Extraídos {len(all_records)} registros...")

        return all_records
    
    def __del__(self):
        """Cierra la sesión al destruir el objeto."""
        if hasattr(self, 'session'):
            self.session.close()
