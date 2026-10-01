import os
import sqlite3

# Configuracion profesional
DB_DIR = "database"
DB_NAME = "mi_base.db"
DB_PATH = os.path.join(DB_DIR, DB_NAME)


def inicializar_sistema():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)


# Conexion local db
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Crear una tabla de prueba
cursor.execute(
    """
  CREATE TABLE IF NOT EXISTS user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  rol TEXT NOT NULL
  )
  """
)
conn.commit()
print("\nTabla creada correctamente\n")
conn.close()


def registrar_prueba(name, rol):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user (name, rol) VALUES (?, ?)", (name, rol))
    conn.commit()
    conn.close()


def consultar_usuarios():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user")
    filas = cursor.fetchall()
    conn.close()
    return filas


if __name__ == "__main__":
    print("--- INICIANDO PRUEBA DE ENTORNO ---")

# Pasos del Debugger
inicializar_sistema()

nombre_test = "Javier"
rol_test = "Administrador"
registrar_prueba(nombre_test, rol_test)

# Verificacion final de la db
usuarios = consultar_usuarios()
print("\n[Exito] Conexion a SQLite Correcta. Registros encontrados:\n")
for u in usuarios:
    print(f"ID: {u[0]}  |  Nombre: {u[1]}  |  Rol: {u[2]}")

print("\n--- PRUEBA FINALIZADA CON EXITO ---")
input("\nPresiona ENTER para cerrar esta ventana...")
