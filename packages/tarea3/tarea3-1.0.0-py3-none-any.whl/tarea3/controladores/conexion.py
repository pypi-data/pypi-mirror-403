"""
Módulo para la conexión con la base de datos.
"""

import sqlite3
import os

"""clase que gestiona la conexion con la base de datos de SQLite, al ser esta la base de datos utilizada 
		no se requiere de user ni pass, ya que Se basa únicamente en un archivo (.db)
"""

# metodo para crear la conexion con la BBDD    
def CZN_CrearConexion():
    try:
        # carpeta donde está ESTE archivo (conexion.py)
        base_dir = os.path.dirname(__file__)

        # construir ruta a modelo/reservas.db
        rutaBD = os.path.join(base_dir, "..", "modelo", "reservas.db")
        rutaBD = os.path.abspath(rutaBD)

        conexion = sqlite3.connect(rutaBD)
        cursor = conexion.cursor()
        return conexion, cursor
    except Exception as e:
        print(f"Error al conectar con la base de datos. Inténtalo de nuevo: {e}")
        return None, None

# ================== CONSULTAS CON LA BASE DE DATOS ==================


# metodo para obtener todos los salones
def CZN_obtener_salones():
    conexion, cursor = CZN_CrearConexion()
    if not conexion: return []
    cursor.execute("SELECT salon_id, nombre FROM salones ORDER BY nombre")
    datos = cursor.fetchall()
    conexion.close()
    return datos

# metodo para obtener el tipo de reserva
def CZN_obtener_tipos_reserva():
    conexion, cursor = CZN_CrearConexion()
    if not conexion: return []
    cursor.execute("""
        SELECT tipo_reserva_id, nombre, requiere_jornadas, requiere_habitaciones
        FROM tipos_reservas
    """)
    datos = cursor.fetchall()
    conexion.close()
    return datos

# metodo para obtener el tipo de cocina
def CZN_obtener_tipos_cocina():
    conexion, cursor = CZN_CrearConexion()
    if not conexion: return []
    cursor.execute("SELECT tipo_cocina_id, nombre FROM tipos_cocina")
    datos = cursor.fetchall()
    conexion.close()
    return datos

# metodo para obtener reservas usando el id del salon como parametro
def CZN_obtener_reservas_por_salon(id_salon):
    conexion, cursor = CZN_CrearConexion()
    if not conexion: return []
    cursor.execute("""
        SELECT r.reserva_id, r.fecha, r.persona, r.telefono, tr.nombre
        FROM reservas r
        JOIN tipos_reservas tr ON r.tipo_reserva_id = tr.tipo_reserva_id
        WHERE r.salon_id = ?
        ORDER BY date(substr(r.fecha, 7, 4) || '-' ||
                      substr(r.fecha, 4, 2) || '-' ||
                      substr(r.fecha, 1, 2)) DESC
    """, (id_salon,))
    datos = cursor.fetchall()
    conexion.close()
    return datos

# metodo para obtener una reserva unsando el id de la reserva como parametro
def CZN_obtener_reserva(reserva_id):
    conexion, cursor = CZN_CrearConexion()
    if not conexion: return None
    cursor.execute("""
        SELECT reserva_id, tipo_reserva_id, salon_id, tipo_cocina_id,
               persona, telefono, fecha, ocupacion, jornadas, habitaciones
        FROM reservas WHERE reserva_id = ?
    """, (reserva_id,))
    datos = cursor.fetchone()
    conexion.close()
    return datos

# ================== INSERT / UPDATE ==================


# metodo para insertar una reserva
def CZN_insertar_reserva(datos):
    conexion, cursor = CZN_CrearConexion()
    if not conexion: return False

    try:
        cursor.execute("""
            INSERT INTO reservas
            (tipo_reserva_id, salon_id, tipo_cocina_id, persona,
             telefono, fecha, ocupacion, jornadas, habitaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos["tipo_reserva_id"],
            datos["salon_id"],
            datos["tipo_cocina_id"],
            datos["persona"],
            datos["telefono"],
            datos["fecha"],
            datos["ocupacion"],
            datos["jornadas"],
            datos["habitaciones"]
        ))
        conexion.commit()
        return True
    except Exception as e:
        print("ERROR SQL:", e)
        conexion.rollback()
        return str(e)
    finally:
        conexion.close()

# metodo para actualizar una reserva concreta
def CZN_actualizar_reserva(reserva_id, datos):
    conexion, cursor = CZN_CrearConexion()
    if not conexion: return False

    try:
        cursor.execute("""
            UPDATE reservas SET
              tipo_reserva_id=?, salon_id=?, tipo_cocina_id=?,
              persona=?, telefono=?, fecha=?, ocupacion=?,
              jornadas=?, habitaciones=?
            WHERE reserva_id=?
        """, (
            datos["tipo_reserva_id"],
            datos["salon_id"],
            datos["tipo_cocina_id"],
            datos["persona"],
            datos["telefono"],
            datos["fecha"],
            datos["ocupacion"],
            datos["jornadas"],
            datos["habitaciones"],
            reserva_id
        ))
        conexion.commit()
        return True
    except Exception as e:
        print("ERROR SQL:", e)
        conexion.rollback()
        return str(e)
    finally:
        conexion.close()