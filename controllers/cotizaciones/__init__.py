"""
Controller: Cotizaciones
Expone únicamente la función de sincronización pública.
"""

import importlib.util
from pathlib import Path

# Cargar el módulo directamente
spec = importlib.util.spec_from_file_location(
    "cotizaciones_controller",
    Path(__file__).parent / "cotizaciones.controller.py"
)
_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_module)

# Exportar funciones
sync = _module.sync
run = _module.run

__all__ = ['sync', 'run']
