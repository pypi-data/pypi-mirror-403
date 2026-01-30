# ==========================================================
# ARCHIVO: datos.py
# DESCRIPCIÓN:
# Este archivo pertenece a la capa de datos del proyecto.
# Se encarga de gestionar la conexión a la base de datos
# SQLite y de ejecutar las consultas necesarias para
# trabajar con salones y reservas.
# ==========================================================

import os
import sqlite3
# Librería estándar de Python para trabajar con bases de datos SQLite


# ==========================================================
# CONFIGURACIÓN DE LA BASE DE DATOS
# ==========================================================

# Ruta donde se encuentra el archivo de la base de datos
BASE_DIR = os.path.dirname(__file__)
RUTA_DB = os.path.join(BASE_DIR, "reservas.db")


def conectar():
    """
    Abre una conexión con la base de datos SQLite y
    activa el uso de claves foráneas para mantener
    la integridad de los datos.
    """
    # Se establece la conexión con la base de datos
    con = sqlite3.connect(RUTA_DB)

    # Se activan las claves foráneas (por defecto están desactivadas en SQLite)
    con.execute("PRAGMA foreign_keys = ON")

    # Se devuelve la conexión creada
    return con


# ==========================================================
# SALONES
# ==========================================================

def obtener_salones():
    """
    Obtiene todos los salones almacenados en la base de datos.

    :return: lista de tuplas con el id y el nombre del salón
    """
    # Se abre la conexión usando un contexto seguro
    with conectar() as con:

        # Se crea el cursor para ejecutar consultas SQL
        cur = con.cursor()

        # Consulta SQL para obtener los salones ordenados por id
        cur.execute("""
            SELECT salon_id, nombre
            FROM salones
            ORDER BY salon_id
        """)

        # Se devuelven todos los resultados obtenidos
        return cur.fetchall()


# ==========================================================
# RESERVAS POR SALÓN
# ==========================================================

def obtener_reservas_por_salon(salon_id):
    """
    Obtiene todas las reservas de un salón concreto.

    :param salon_id: identificador del salón seleccionado
    :return: lista de reservas asociadas al salón
    """
    # Se abre la conexión a la base de datos
    with conectar() as con:

        # Cursor para ejecutar la consulta
        cur = con.cursor()

        # Consulta SQL que obtiene las reservas y sus datos relacionados
        cur.execute("""
            SELECT 
                r.reserva_id,
                r.fecha,
                r.persona,
                r.telefono,
                tr.nombre,
                tc.nombre,
                r.ocupacion,
                r.jornadas,
                r.habitaciones
            FROM reservas r
            JOIN tipos_reservas tr 
                ON r.tipo_reserva_id = tr.tipo_reserva_id
            JOIN tipos_cocina tc
                ON r.tipo_cocina_id = tc.tipo_cocina_id
            WHERE r.salon_id = ?
            ORDER BY r.fecha DESC
        """, (salon_id,))

        # Se devuelven todas las reservas encontradas
        return cur.fetchall()


# ==========================================================
# TIPOS DE RESERVA
# ==========================================================

def obtener_tipos_reserva():
    """
    Obtiene los tipos de reserva disponibles.

    :return: lista de tipos de reserva
    """
    with conectar() as con:
        cur = con.cursor()

        # Consulta para obtener los tipos de reserva
        cur.execute("""
            SELECT tipo_reserva_id, nombre
            FROM tipos_reservas
            ORDER BY tipo_reserva_id
        """)

        return cur.fetchall()


# ==========================================================
# TIPOS DE COCINA
# ==========================================================

def obtener_tipos_cocina():
    """
    Obtiene los tipos de cocina disponibles.

    :return: lista de tipos de cocina
    """
    with conectar() as con:
        cur = con.cursor()

        # Consulta para obtener los tipos de cocina
        cur.execute("""
            SELECT tipo_cocina_id, nombre
            FROM tipos_cocina
            ORDER BY tipo_cocina_id
        """)

        return cur.fetchall()


# ==========================================================
# INSERTAR RESERVA
# ==========================================================

def insertar_reserva(datos_reserva):
    """
    Inserta una nueva reserva en la base de datos.

    :param datos_reserva: tupla con los datos de la reserva
    :return: True si la inserción es correcta,
             False y mensaje de error si falla
    """
    try:
        # Se abre la conexión a la base de datos
        with conectar() as con:
            cur = con.cursor()

            # Consulta SQL para insertar una nueva reserva
            cur.execute("""
                INSERT INTO reservas
                (tipo_reserva_id, salon_id, tipo_cocina_id,
                 persona, telefono, fecha, ocupacion,
                 jornadas, habitaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, datos_reserva)

        # Si todo va bien, se devuelve éxito
        return True, ""

    except sqlite3.IntegrityError:
        # Error por violación de claves únicas o foráneas
        return False, "Ya existe una reserva para ese salón en esa fecha"


# ==========================================================
# ACTUALIZAR RESERVA
# ==========================================================

def actualizar_reserva(reserva_id, datos_reserva):
    """
    Actualiza una reserva existente en la base de datos.

    :param reserva_id: identificador de la reserva
    :param datos_reserva: tupla con los nuevos datos
    :return: True si la actualización es correcta,
             False y mensaje de error si falla
    """
    try:
        with conectar() as con:
            cur = con.cursor()

            # Consulta SQL para actualizar los datos de la reserva
            cur.execute("""
                UPDATE reservas SET
                    tipo_reserva_id = ?,
                    salon_id = ?,
                    tipo_cocina_id = ?,
                    persona = ?,
                    telefono = ?,
                    fecha = ?,
                    ocupacion = ?,
                    jornadas = ?,
                    habitaciones = ?
                WHERE reserva_id = ?
            """, (*datos_reserva, reserva_id))

        return True, ""

    except sqlite3.IntegrityError:
        return False, "Ya existe una reserva para ese salón en esa fecha"




