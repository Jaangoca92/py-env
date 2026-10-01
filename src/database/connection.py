import sqlite3
from config.settings import DB_PATH
from sqlite3 import Error


def get_connection():
    """Establece y retorna la conexion a la base de datos SQLite."""
    connection = None
    try:
        connection = sqlite3.connect(str(DB_PATH))
        # Habilitar el soporte para llaves foraneas (muy importante en diseno relacional)
        connection.execute("PRAGMA foreign_keys = ON;")
        return connection
    except Error as e:
        print(f"Error al conectar a la base de datos: {e}")
        if connection:
            connection.close()
        return None


def execute_query(query, params=None):
    """
    Ejecuta consultas de insercion, actualizacion o eliminacion (INSERT, UPDATE, DELETE).
    Usa un administrador de contexto para asegurar que los cambios se guarden (commit)
    y que la conexion  se cierre de forma segura.
    """
    connection = get_connection()
    if connection is None:
        return False
    try:
        with connection:  # Hace COMMIT automaticamente si todo sale bien, o ROLLBACK si hay error)
            cursor = connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
        return True
    except Error as e:
        print(f"Error a ejecutar la consulta: {e}")
        return False
    finally:
        connection.close()


def fetch_query(query, params=None):
    """
    Ejecuta consultas de seleccion (SELECT) y devuelve todos los resultados.
    """
    connection = get_connection()
    if connection is None:
        return []
    try:
        cursor = connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()
    except Error as e:
        print(f"Error al consultar los datos: {e}")
        return []
    finally:
        connection.close()


if __name__ == "__main__":
    print("\nProbando la conexion de manera directa...")
    con = get_connection()
    if con:
        print("Conexion profesional exitosa a SQLite3!")
        con.close()  # La cerramos de inmediato para no dejar el archivo bloqueado.
    else:
        print("No se pudo establecer la conexion")
