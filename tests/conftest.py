import os
import sys

# Agregar las carpetas del proyecto al PYTHONPATH
TRAFFIC_SUMO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for folder in ["controller", "analysis", "tools", "."]:
    p = os.path.join(TRAFFIC_SUMO_DIR, folder)
    if p not in sys.path:
        sys.path.insert(0, p)
