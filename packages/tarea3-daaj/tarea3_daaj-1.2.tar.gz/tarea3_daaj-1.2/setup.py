# Importamos las funciones necesarias de setuptools
from setuptools import setup, find_packages

# Llamada principal para definir la distribución del paquete
setup(
    # Nombre del paquete (así se instalará con pip)
    name="tarea3-daaj",

    # Versión del proyecto
    version="1.2",

    # Descripción breve de la aplicación
    description="Aplicación de gestión de reservas",

    # Autor del proyecto
    author="Diego Alexander Albarracín Jacho",

    # Busca automáticamente todos los paquetes Python
    # (carpetas que tienen __init__.py)
    packages=find_packages(),

    # Indica que también se incluyan ficheros que no son .py
    include_package_data=True,

    # Lista de ficheros extra que debe empaquetar setuptools
    # dentro del paquete tarea3
    package_data={
        "tarea3": [
            "modelos/*.db",      # Base de datos SQLite
            "modelos/*.sql",     # Script SQL
            "recursos/img/*",    # Imágenes de la aplicación
            "vistas/*.ui"        # Archivos de interfaz gráfica Qt
        ]
    },

    # Scripts ejecutables a instalar con el paquete
    # Se deja vacío porque la app se ejecuta como módulo:
    # python -m tarea3.principal
    scripts=[],
)

