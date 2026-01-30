# ==========================================================
# ARCHIVO: main.py
# DESCRIPCIÓN:
# Archivo principal de la aplicación. Se encarga de iniciar
# la interfaz gráfica, mostrar una pantalla de carga
# (Splash Screen) y, tras unos segundos, abrir el menú
# principal.
# ==========================================================

import sys
import os

from PySide6.QtWidgets import QApplication, QSplashScreen, QMessageBox
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QTimer

from tarea3.controladores.menu import DAAJ_Menu

def resource_path(relative_path):
    """
    Devuelve la ruta correcta a un recurso tanto en modo normal
    como cuando la aplicación está empaquetada con PyInstaller.
    """
    try:
        # Cuando está en un .exe de PyInstaller
        base_path = sys._MEIPASS
    except Exception:
        # Cuando se ejecuta como script normal
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)



def main():
    """
    Función principal de la aplicación.

    - Inicializa la aplicación Qt.
    - Muestra una pantalla de carga con el logo.
    - Tras un tiempo de espera, abre el menú principal.
    """

    # Creación de la aplicación Qt (obligatoria)
    app = QApplication(sys.argv)

    # ======================================================
    # CONFIGURACIÓN DE LA PANTALLA DE CARGA (SPLASH SCREEN)
    # ======================================================
    
    # Ruta completa del logo de la aplicación
    logo_path = resource_path("tarea3/recursos/img/logo.jpg")

    # Comprobación de que el archivo del logo existe
    if not os.path.exists(logo_path):
        QMessageBox.critical(
            None,
            "Error",
            "No se ha encontrado el logo de la aplicación"
        )
        sys.exit(1)

    # Carga del logo y redimensionado manteniendo proporciones
    pixmap = QPixmap(logo_path).scaled(
        600,
        600,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation
    )

    # Creación de la pantalla de carga
    splash = QSplashScreen(pixmap)

    # Hace que la ventana se mantenga por delante
    splash.setWindowFlag(Qt.WindowStaysOnTopHint)

    # Mostrar la pantalla de carga
    splash.show()
    splash.raise_()

    # Variable para mantener referencia al menú principal
    ventana_menu = None

    def mostrar_menu():
        """
        Cierra la pantalla de carga y muestra el menú principal.
        Se ejecuta tras el tiempo de espera definido.
        """
        nonlocal ventana_menu

        # Creación del menú principal
        ventana_menu = DAAJ_Menu()

        # Finaliza el splash cuando el menú está listo
        splash.finish(ventana_menu)

        # Mostrar el menú principal
        ventana_menu.show()

    # Espera de 2 segundos antes de mostrar el menú
    QTimer.singleShot(2000, mostrar_menu)

    # Inicio del bucle principal de la aplicación
    sys.exit(app.exec())


# Punto de entrada del programa
if __name__ == "__main__":
    main()











