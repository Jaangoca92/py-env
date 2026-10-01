# Main DB profesional proyecto

from database.database_init import init_db
from models import user_model


def main():
    # 1 Asegurar que las tablas existan al arrancar
    init_db()
    print("\n--- Ejecutando pruebas del sistema CRUD ---")

    # 2 Insertar usuarios de prueba (C)
    print("\nRegistrando usuarios nuevos...")
    user_model.create_user("Javier Gomez", "javier@email.com", rol_id=1)
    user_model.create_user("Adrian Hoyos", "adrian@email.com", rol_id=2)

    # 3 Consultar y mostrar usuarios (R)
    print("\nLista actual de usuarios en el sistema:")
    usuarios = user_model.get_all_users()
    if usuarios:
        for user in usuarios:
            print(
                f"\nID: {user[0]}  |  Nombre: {user[1]}  |  Email: {user[2]}  |  Rol: {user[3]}"
            )
    else:
        print("No se encontraron registros.")

    # 4 Modificar un registro (U)
    print("\nActualizando datos de Adrian...")
    user_model.update_user_email(2, "adrian2@email.com")

    # 5 Volver a consultar para verificar el cambio
    print("\nLista actualizada:\n")
    for user in user_model.get_all_users():
        print(
            f"ID: {user[0]}  |  Nombre: {user[1]}  |   Email: {user[2]}   |  Rol: {user[3]}"
        )

    # 6 Eliminar usuario
    print("\nEliminando al usuario con ID 1 (Javier Gomez)...")
    user_model.delete_user(1)

    # Consulta final para verificar que se elimino correctamente
    print("\nLista final tras la eliminacion:\n")
    usuarios = user_model.get_all_users()
    if usuarios:
        for user in usuarios:
            print(
                f"ID: {user[0]}  |  Nombre: {user[1]}  |  Email: {user[2]}  |  Rol: {user[3]}"
            )
    else:
        print("No se encontraron registros.")


if __name__ == "__main__":
    main()
