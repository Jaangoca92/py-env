# Importamosdesde el mismo paquete usando el punto (.) que significa "Esta misma carpeta"
from .connection import execute_query


def init_db():
    """Crea las tablas automaticamente si no existen al iniciar el proyecto."""
    print("\nVerificando e inicializando tablas de la base de datos...")

    # Tabla de roles (Ejemplo de catalogo)
    create_roles_table = """
    CREATE TABLE IF NOT EXISTS roles(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nombre TEXT NOT NULL UNIQUE
    );
    """

    # Tabla de usuarios relacionada con roles
    create_users_table = """
    CREATE TABLE IF NOT EXISTS usuarios(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      nombre TEXT NOT NULL,
      email TEXT UNIQUE NOT NULL,
      rol_id INTEGER,
      FOREIGN KEY (rol_id) REFERENCES roles(id) ON DELETE SET NULL
    );
    """
    execute_query(create_roles_table)
    execute_query(create_users_table)
    print("\nEstructuras de tablas verificadas con exito!")
    _insert_default_roles()


def _insert_default_roles():
    """Inserta datos iniciales de forma segura."""
    execute_query(
        "INSERT OR IGNORE INTO roles(id, nombre) VALUES (1, 'Administrador');"
    )
    execute_query("INSERT OR IGNORE INTO roles(id, nombre) VALUES (2, 'Usuario')")
