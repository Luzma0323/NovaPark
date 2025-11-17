import sqlite3
import os
import sys
from tkinter import messagebox

def conectar_bd_parqueaderojmj():
    try:
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(__file__)

        db_path = os.path.join(base_dir, "parqueaderojmj.db")

        if not os.path.exists(db_path):
            messagebox.showerror("Base de Datos no encontrada",
                                 f"No se encontró la base de datos en:\n{db_path}\n\nAsegúrate de copiar 'parqueaderojmj.db' (y sus archivos -shm/-wal) a la carpeta donde está el ejecutable.")
            return None

        conexion = sqlite3.connect(db_path)
        conexion.execute("PRAGMA journal_mode=WAL")
        conexion.execute("PRAGMA busy_timeout = 10000")
        return conexion
    except sqlite3.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos SQLite.\nError: {err}")
        return None

def ejecutar_consulta(query, parametros=()):
    """Ejecuta una consulta en la base de datos y maneja automáticamente la conexión."""
    conexion = conectar_bd_parqueaderojmj()
    if conexion is None:
        return None
    try:
        cursor = conexion.cursor()
        cursor.execute(query, parametros)
        conexion.commit()
        return cursor
    except sqlite3.Error as err:
        print(f"Error al ejecutar la consulta: {err}")
        messagebox.showerror("Error de Base de Datos", f"Ocurrió un error al ejecutar la consulta.\nError: {err}")
        return None
    finally:
        conexion.close()

def verificar_esquema_tabla(nombre_tabla):
    conexion = conectar_bd_parqueaderojmj()
    if conexion is None:
        return None
    try:
        cursor = conexion.cursor()
        cursor.execute(f"PRAGMA table_info({nombre_tabla})")
        columnas = cursor.fetchall()
        return [columna[1] for columna in columnas]
    except sqlite3.Error as err:
        print(f"Error al verificar el esquema de la tabla {nombre_tabla}: {err}")
        messagebox.showerror("Error de Base de Datos", f"No se pudo verificar el esquema de la tabla {nombre_tabla}.")
        return None
    finally:
        conexion.close()

def verificar_bloqueo():
    conexion = conectar_bd_parqueaderojmj()
    if conexion is None:
        return False
    try:
        cursor = conexion.cursor()
        cursor.execute("PRAGMA database_list;")
        print("Base de datos accesible.")
        return True
    except sqlite3.OperationalError as err:
        print(f"La base de datos está bloqueada: {err}")
        return False
    finally:
        conexion.close()