# ==========================================================
# ARCHIVO: mostrar_reservas.py
# DESCRIPCIÓN:
# Ventana principal encargada de mostrar los salones
# disponibles y las reservas asociadas a cada uno.
# Desde esta ventana se pueden crear nuevas reservas
# o editar las existentes.
# ==========================================================

from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
    QAbstractItemView
)
from PySide6.QtCore import Qt

from tarea3.vistas.mostrar_reservas import Ui_DAAJ_MostrarReservas
from tarea3.modelos import datos
from tarea3.controladores.reservar import DAAJ_Reservar


class MostrarReservas(QMainWindow):
    """
    Ventana DAAJ · Mostrar reservas

    Permite:
    - Seleccionar un salón
    - Visualizar las reservas del salón seleccionado
    - Crear nuevas reservas
    - Editar reservas existentes
    """

    def __init__(self):
        """Constructor de la ventana principal."""
        super().__init__()

        # Carga de la interfaz gráfica
        self.ui = Ui_DAAJ_MostrarReservas()
        self.ui.setupUi(self)

        # Título de la ventana
        self.setWindowTitle("DAAJ · Mostrar reservas")

        # ==================================================
        # CONFIGURACIÓN DE LA TABLA DE RESERVAS
        # ==================================================

        # La tabla es solo de lectura
        self.ui.daaj_tblReservas.setEditTriggers(
            QAbstractItemView.NoEditTriggers
        )

        # Selección por filas completas
        self.ui.daaj_tblReservas.setSelectionBehavior(
            QAbstractItemView.SelectRows
        )

        # Solo se permite seleccionar una fila
        self.ui.daaj_tblReservas.setSelectionMode(
            QAbstractItemView.SingleSelection
        )

        # Número de columnas reales (según la base de datos)
        self.ui.daaj_tblReservas.setColumnCount(8)

        # Títulos de las columnas visibles
        self.ui.daaj_tblReservas.setHorizontalHeaderLabels([
            "Fecha",
            "Persona",
            "Teléfono",
            "Tipo reserva",
            "Tipo cocina",
            "Personas",
            "Jornadas",
            "Habitaciones"
        ])

        # Diccionario para relacionar nombre del salón con su id
        self._salones = {}

        # Identificador del salón seleccionado
        self.salon_id_seleccionado = None

        # Carga inicial de los salones
        self._cargar_salones()

        # ==================================================
        # SEÑALES Y EVENTOS
        # ==================================================

        # Selección de un salón
        self.ui.daaj_lstSalones.itemClicked.connect(
            self._mostrar_reservas
        )

        # Botón para crear o editar reservas
        self.ui.daaj_btnReservar.clicked.connect(
            self._abrir_reserva
        )

    # ==================================================
    # CARGAR SALONES
    # ==================================================

    def _cargar_salones(self):
        """
        Carga la lista de salones disponibles desde la base de datos.
        """
        # Limpia la lista de salones
        self.ui.daaj_lstSalones.clear()

        # Obtiene los salones y los añade a la lista
        for salon_id, nombre in datos.obtener_salones():
            self._salones[nombre] = salon_id
            self.ui.daaj_lstSalones.addItem(nombre)

    # ==================================================
    # MOSTRAR RESERVAS DEL SALÓN SELECCIONADO
    # ==================================================

    def _mostrar_reservas(self):
        """
        Muestra en la tabla las reservas del salón seleccionado.
        """
        item = self.ui.daaj_lstSalones.currentItem()
        if not item:
            return

        # Obtiene el id del salón seleccionado
        nombre = item.text()
        self.salon_id_seleccionado = self._salones[nombre]

        # Obtiene las reservas del salón desde la base de datos
        reservas = datos.obtener_reservas_por_salon(
            self.salon_id_seleccionado
        )

        # Limpia la tabla
        self.ui.daaj_tblReservas.setRowCount(0)

        # Rellena la tabla con las reservas
        for fila, reserva in enumerate(reservas):
            self.ui.daaj_tblReservas.insertRow(fila)

            # El id de la reserva no se muestra, se guarda internamente
            reserva_id = reserva[0]

            for col, valor in enumerate(reserva[1:]):
                item = QTableWidgetItem(str(valor))

                # Se guarda el id de la reserva en el item
                item.setData(Qt.UserRole, reserva_id)

                self.ui.daaj_tblReservas.setItem(fila, col, item)

    # ==================================================
    # ABRIR DIÁLOGO DE RESERVA
    # ==================================================

    def _abrir_reserva(self):
        """
        Abre el diálogo para crear una nueva reserva
        o editar la reserva seleccionada.
        """
        # Comprobación de que hay un salón seleccionado
        if not self.salon_id_seleccionado:
            QMessageBox.warning(
                self, "Aviso", "Seleccione un salón primero"
            )
            return

        # Fila seleccionada en la tabla
        fila = self.ui.daaj_tblReservas.currentRow()

        # --------------------------------------------------
        # EDITAR RESERVA EXISTENTE
        # --------------------------------------------------
        if fila >= 0:

            # Función auxiliar para obtener texto de una columna
            def texto(col):
                item = self.ui.daaj_tblReservas.item(fila, col)
                return item.text() if item else ""

            # Obtiene el id de la reserva almacenado en la tabla
            reserva_id = self.ui.daaj_tblReservas.item(
                fila, 0
            ).data(Qt.UserRole)

            # Construye el diccionario de la reserva
            reserva = {
                "reserva_id": reserva_id,
                "fecha": texto(0),
                "persona": texto(1),
                "telefono": texto(2),
                "tipo_reserva": texto(3),
                "tipo_cocina": texto(4),
                "ocupacion": int(texto(5)),
                "jornadas": int(texto(6)),
                "habitaciones": int(texto(7))
            }

            # Abre el diálogo en modo edición
            dlg = DAAJ_Reservar(
                self.salon_id_seleccionado,
                reserva
            )

        # --------------------------------------------------
        # NUEVA RESERVA
        # --------------------------------------------------
        else:
            # Abre el diálogo en modo nueva reserva
            dlg = DAAJ_Reservar(self.salon_id_seleccionado)

        # Si se guarda la reserva, se recarga la tabla
        if dlg.exec():
            self._mostrar_reservas()









