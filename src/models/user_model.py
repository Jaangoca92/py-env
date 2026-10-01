from database.connection import execute_query, fetch_query


def create_user(nombre, email, rol_id=2):
    """Inserta un nuevo usuario (CREATE)."""
    query = "INSERT INTO usuarios(nombre, email, rol_id) VALUES (?,?,?);"
    return execute_query(query, (nombre, email, rol_id))


def get_all_users():
    """Obtiene todos los usuariosuniendo sus nombres de rol (READ)."""
    query = """
  SELECT u.id, u.nombre, u.email, r.nombre
  FROM usuarios u
  LEFT JOIN roles r ON u.rol_id = r.id;
  """
    return fetch_query(query)


def update_user_email(user_id, nuevo_email):
    """Actualiza el correo de un usuario (UPDATE)."""
    query = "UPDATE usuarios SET email = ? WHERE id = ?;"
    return execute_query(query, (nuevo_email, user_id))


def delete_user(user_id):
    """Elimina un usuario de forma definitva(DELETE)."""
    query = "DELETE FROM usuarios WHERE id = ?;"
    return execute_query(query, (user_id,))
