# ==========================================================
# ARCHIVO: menu.py
# DESCRIPCIÓN:
# Ventana principal (menú) de la aplicación DAAJ.
# Desde esta ventana se accede a la gestión de reservas
# y se muestra una imagen de fondo a pantalla completa.
# ==========================================================

import os

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt

from tarea3.vistas.menu import Ui_DAAJ_Menu
from tarea3.controladores.mostrar_reservas import MostrarReservas


class DAAJ_Menu(QMainWindow):
    """
    Ventana principal (Menú) de la aplicación DAAJ.

    Muestra el menú principal con una imagen de fondo
    y permite acceder a la ventana de gestión de reservas.
    """

    def __init__(self):
        """Constructor del menú principal."""
        super().__init__()

        # ==================================================
        # CARGA DE LA INTERFAZ GRÁFICA
        # ==================================================

        # Se carga la interfaz creada con Qt Designer
        self.ui = Ui_DAAJ_Menu()
        self.ui.setupUi(self)

        # Título de la ventana
        self.setWindowTitle("DAAJ · Menú principal")

        # Centra la ventana en la pantalla
        self._centrar_ventana()

        # ==================================================
        # CONFIGURACIÓN DE LA IMAGEN DE FONDO
        # ==================================================

        # Ruta base del proyecto
        base_path = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        # Ruta completa de la imagen de fondo
        ruta = os.path.join(
            base_path, "recursos", "img", "fondo_menu.jpg"
        )

        # Normaliza la ruta para evitar problemas en Windows
        ruta = ruta.replace("\\", "/")

        # Se establece la imagen de fondo solo en el centralwidget
        self.ui.centralwidget.setStyleSheet(f"""
            QWidget#centralwidget {{
                border-image: url("{ruta}") 0 0 0 0 stretch stretch;
            }}
        """)

        # ==================================================
        # CONFIGURACIÓN DE TRANSPARENCIA Y ESTILO
        # ==================================================

        # Hace transparente el fondo del logo
        self.ui.daaj_lblLogo.setStyleSheet("background: transparent;")

        # Estilo del título del menú
        self.ui.daaj_lblTitulo.setStyleSheet("""
            background: transparent;
            color: white;
            font-size: 18px;
        """)

        # ==================================================
        # SEÑALES DEL MENÚ
        # ==================================================

        # Acción para abrir la gestión de reservas
        self.ui.daaj_actReservas.triggered.connect(
            self._daaj_abrir_reservas
        )

        # Acción para salir de la aplicación
        self.ui.daaj_actSalir.triggered.connect(self.close)

        # Referencia a la ventana de reservas
        self.daaj_ventana_reservas = None

    # ==================================================
    # CENTRAR VENTANA
    # ==================================================

    def _centrar_ventana(self):
        """
        Centra la ventana en la pantalla actual.
        """
        qr = self.frameGeometry()
        cp = self.screen().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    # ==================================================
    # ABRIR GESTIÓN DE RESERVAS
    # ==================================================

    def _daaj_abrir_reservas(self):
        """
        Abre la ventana de gestión de reservas.
        Si ya está abierta, la trae al primer plano.
        """
        if self.daaj_ventana_reservas is None:
            # Se crea la ventana de reservas
            self.daaj_ventana_reservas = MostrarReservas()

            # Se indica que se elimine al cerrarse
            self.daaj_ventana_reservas.setAttribute(
                Qt.WA_DeleteOnClose
            )

            # Señal para limpiar la referencia al cerrar
            self.daaj_ventana_reservas.destroyed.connect(
                self._daaj_cerrar_reservas
            )

            # Se muestra la ventana
            self.daaj_ventana_reservas.show()
        else:
            # Si ya está abierta, se trae al frente
            self.daaj_ventana_reservas.raise_()
            self.daaj_ventana_reservas.activateWindow()

    # ==================================================
    # CIERRE DE LA VENTANA DE RESERVAS
    # ==================================================

    def _daaj_cerrar_reservas(self):
        """
        Limpia la referencia cuando se cierra
        la ventana de reservas.
        """
        self.daaj_ventana_reservas = None









