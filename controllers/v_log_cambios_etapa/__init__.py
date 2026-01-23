"""Controller: v_log_cambios_etapa"""

import importlib.util
from pathlib import Path

# Cargar el módulo directamente
spec = importlib.util.spec_from_file_location(
    "v_log_cambios_etapa_controller",
    Path(__file__).parent / "v_log_cambios_etapa.controller.py"
)
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)

sync = _module.sync
run = _module.run

__all__ = ['sync', 'run']
