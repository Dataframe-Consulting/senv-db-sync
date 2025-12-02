"""
Configuración centralizada para el sistema de sincronización.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class OracleApexConfig:
    """Configuración para Oracle APEX."""
    base_url: str
    endpoint: str
    username: str
    password: str
    timeout: int = 60
    max_retries: int = 3
    retry_delay: int = 2

    @classmethod
    def from_env(cls, endpoint: str):
        """Crea configuración desde variables de entorno."""
        return cls(
            base_url=os.getenv('ORACLE_APEX_BASE_URL', 'https://gsn.maxapex.net/ords/savio'),
            endpoint=endpoint,
            username=os.getenv('ORACLE_APEX_USERNAME'),
            password=os.getenv('ORACLE_APEX_PASSWORD'),
            timeout=int(os.getenv('REQUEST_TIMEOUT', 60)),
            max_retries=int(os.getenv('MAX_RETRIES', 3)),
            retry_delay=int(os.getenv('RETRY_DELAY', 2))
        )


@dataclass
class SupabaseConfig:
    """Configuración para Supabase."""
    url: str
    key: str
    table_name: str

    @classmethod
    def from_env(cls, table_name: str):
        """Crea configuración desde variables de entorno."""
        return cls(
            url=os.getenv('SUPABASE_URL'),
            key=os.getenv('SUPABASE_KEY'),
            table_name=table_name
        )


@dataclass
class SyncConfig:
    """Configuración general de sincronización."""
    batch_size: int = 1000  # Aumentado de 100 a 1000 para mayor velocidad
    log_level: str = 'INFO'

    @classmethod
    def from_env(cls):
        """Crea configuración desde variables de entorno."""
        return cls(
            batch_size=int(os.getenv('BATCH_SIZE', 1000)),
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
