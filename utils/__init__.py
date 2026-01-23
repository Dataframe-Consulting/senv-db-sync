"""
Utilidades compartidas entre controllers.
Sin conocimiento de dominio específico.
"""

from .http_client import http_get, http_get_all_pages, create_session, close_session
from .supabase_client import (
    get_supabase_client,
    batch_upsert,
    get_max_date,
    count_records
)
from .dates import (
    parse_oracle_date,
    format_date_yyyymmdd,
    get_date_range,
    days_ago
)

__all__ = [
    # HTTP
    'http_get',
    'http_get_all_pages',
    'create_session',
    'close_session',
    
    # Supabase
    'get_supabase_client',
    'batch_upsert',
    'get_max_date',
    'count_records',
    
    # Fechas
    'parse_oracle_date',
    'format_date_yyyymmdd',
    'get_date_range',
    'days_ago',
]
