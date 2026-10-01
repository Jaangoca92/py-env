import os
from pathlib import Path

# Path(__file__) es este archivo (settings.py)
# .parent es la carpeta 'config'
# .parent.parent es la carpeta 'src'
SRC_DIR = Path(__file__).resolve().parent.parent

# Definimos la carpeta 'database' y la ruta completa al archivo '.db'
DB_DIR = SRC_DIR / "database"
DB_PATH = DB_DIR / "my.database.db"

# Asegura que la carpeta 'database' exista si aun no ha sido creada
os.makedirs(DB_DIR, exist_ok=True)
