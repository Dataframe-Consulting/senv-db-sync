"""Controller: v_insumos"""

import importlib.util
from pathlib import Path

# Cargar el módulo directamente
spec = importlib.util.spec_from_file_location(
    "v_insumos_controller",
    Path(__file__).parent / "v_insumos.controller.py"
)
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)

sync = _module.sync
run = _module.run

__all__ = ['sync', 'run']
