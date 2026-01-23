"""Controller: Clientes"""

from importlib import import_module

# Importar el módulo clientes.controller (el archivo se llama clientes.controller.py)
# Python no puede importar directamente archivos con punto en el nombre
# así que usamos importlib con el nombre del archivo completo
import sys
from pathlib import Path

# Cargar el módulo directamente
import importlib.util
spec = importlib.util.spec_from_file_location(
    "clientes_controller",
    Path(__file__).parent / "clientes.controller.py"
)
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)

sync = _module.sync
run = _module.run

__all__ = ['sync', 'run']
