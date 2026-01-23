"""Controller: proyectos_cliente"""

import importlib.util
from pathlib import Path

# Cargar el módulo directamente
spec = importlib.util.spec_from_file_location(
    "proyectos_cliente_controller",
    Path(__file__).parent / "proyectos_cliente.controller.py"
)
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)

sync = _module.sync
run = _module.run

__all__ = ['sync', 'run']
