import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_NAME = "database.db"


def get_db_connection():
    """
    Crea una conexión eficiente a SQLite.
    row_factory permite acceder a los campos por su nombre y no por posición.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa la base de datos y crea la tabla de forma segura."""
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT NOT NULL,
                completada INTEGER DEFAULT 0
            )
        """
        )
        # 'with' realiza el commit de manera automática al finalizar sin errores


# --- RUTAS DE LA API REST ---


@app.route("/tareas", methods=["GET"])
def obtener_tareas():
    """Endpoint para obtener todas las tareas (GET)."""
    try:
        with get_db_connection() as conn:
            filas = conn.execute("SELECT * FROM tareas").fetchall()
            # Convertimos cada fila (sqlite3.Row) a diccionario de Python de forma dinámica
            tareas = [dict(f) for f in filas]
            # Convertimos el entero 0/1 a Booleano (True/False)
            for t in tareas:
                t["completada"] = bool(t["completada"])

        return jsonify(tareas), 200
    except Exception as e:
        return (
            jsonify(
                {
                    "error": "Error interno al consultar la base de datos",
                    "detalle": str(e),
                }
            ),
            500,
        )


@app.route("/tareas", methods=["POST"])
def crear_tarea():
    """Endpoint para crear una nueva tarea (POST)."""
    datos = request.get_json()

    # Validación simple
    if not datos or "titulo" not in datos or not str(datos["titulo"]).strip():
        return (
            jsonify(
                {"error": "El campo 'titulo' es obligatorio y no puede estar vacío"}
            ),
            400,
        )

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO tareas (titulo) VALUES (?)", (datos["titulo"].strip(),)
            )
            id_creado = cursor.lastrowid

        return (
            jsonify(
                {
                    "mensaje": "Tarea creada exitosamente",
                    "tarea": {
                        "id": id_creado,
                        "titulo": datos["titulo"].strip(),
                        "completada": False,
                    },
                }
            ),
            201,
        )
    except Exception as e:
        return jsonify({"error": "Error al guardar la tarea", "detalle": str(e)}), 500


# Endpoint PUT: Actualizar una tarea por su ID
@app.route("/tareas/<int:tarea_id>", methods=["PUT"])
def actualizar_tarea(tarea_id):
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "No se enviaron datos para actualizar"}), 400

    try:
        with get_db_connection() as conn:
            # Verificar si la tarea existe
            tarea = conn.execute(
                "SELECT * FROM tareas WHERE id = ?", (tarea_id,)
            ).fetchone()
            if not tarea:
                return jsonify({"error": "Tarea no encontrada"}), 404

            # Obtener valores actuales o nuevos
            nuevo_titulo = datos.get("titulo", tarea["titulo"]).strip()
            nueva_completada = int(datos.get("completada", tarea["completada"]))

            conn.execute(
                "UPDATE tareas SET titulo = ?, completada = ? WHERE id = ?",
                (nuevo_titulo, nueva_completada, tarea_id),
            )

        return jsonify({"mensaje": f"Tarea {tarea_id} actualizada correctamente"}), 200
    except Exception as e:
        return (
            jsonify({"error": "Error al actualizar la tarea", "detalle": str(e)}),
            500,
        )


# Endpoint DELETE: Eliminar una tarea por su ID
@app.route("/tareas/<int:tarea_id>", methods=["DELETE"])
def eliminar_tarea(tarea_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
            if cursor.rowcount == 0:
                return jsonify({"error": "Tarea no encontrada"}), 404

        return jsonify({"mensaje": f"Tarea {tarea_id} eliminada correctamente"}), 200
    except Exception as e:
        return jsonify({"error": "Error al eliminar la tarea", "detalle": str(e)}), 500


# --- EJECUCIÓN DE LA APLICACIÓN ---

if __name__ == "__main__":
    # Inicialización controlada al ejecutar directamente app.py
    init_db()
    # Ejecución con host 0.0.0.0 y puerto 5000
    app.run(host="0.0.0.0", port=5000, debug=True)

# curl http://localhost:5000/tareas
# curl -X POST -H "Content-Type: application/json" -d "{\"titulo\":\"Mi primera tarea profesional\"}" http://localhost:5000/tareas
# curl -X PUT http://127.0.0.1:5000/tareas/1 -H "Content-Type: application/json" -d "{\"completada\": true}"
# curl -X DELETE http://127.0.0.1:5000/tareas/1
