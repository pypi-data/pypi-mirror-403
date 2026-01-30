# ==========================================================
# ARCHIVO: reservar.py
# DESCRIPCIÓN:
# Diálogo encargado de crear y editar reservas.
# Permite introducir los datos de una reserva,
# validarlos y guardarlos en la base de datos.
# ==========================================================

from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import QDate

from tarea3.vistas.reservar import Ui_DAAJ_Reservar
from tarea3.modelos import datos


class DAAJ_Reservar(QDialog):
    """
    Diálogo DAAJ · Reservar

    Ventana modal que permite crear una nueva reserva
    o editar una existente según el contexto.
    """

    def __init__(self, id_salon, reserva=None):
        """
        Constructor del diálogo de reservas.

        :param id_salon: identificador del salón seleccionado
        :param reserva: datos de la reserva (None si es nueva)
        """
        super().__init__()

        # Carga de la interfaz gráfica creada con Qt Designer
        self.ui = Ui_DAAJ_Reservar()
        self.ui.setupUi(self)

        # Datos recibidos
        self.id_salon = id_salon
        self.reserva = reserva
        self.es_edicion = reserva is not None

        # Título de la ventana según el modo
        self.setWindowTitle(
            "DAAJ · Editar reserva"
            if self.es_edicion
            else "DAAJ · Nueva reserva"
        )

        # ==================================================
        # CONFIGURACIÓN DEL CAMPO FECHA
        # ==================================================

        # Habilita el calendario desplegable
        self.ui.daaj_dateEvento.setCalendarPopup(True)

        # Formato de fecha estándar
        self.ui.daaj_dateEvento.setDisplayFormat("yyyy-MM-dd")

        # Fecha actual por defecto en nuevas reservas
        if not self.es_edicion:
            self.ui.daaj_dateEvento.setDate(QDate.currentDate())

        # ==================================================
        # TIPOS DE RESERVA
        # ==================================================

        # Diccionario para relacionar texto con id
        self.tipos_reserva = {}
        self.ui.daaj_cmbTipoReserva.clear()

        # Carga de los tipos de reserva desde la base de datos
        for tipo_id, nombre in datos.obtener_tipos_reserva():
            self.tipos_reserva[nombre] = tipo_id
            self.ui.daaj_cmbTipoReserva.addItem(nombre)

        # ==================================================
        # TIPOS DE COCINA
        # ==================================================

        # Diccionario para relacionar texto con id
        self.tipos_cocina = {}
        self.ui.daaj_cmbTipoCocina.clear()

        # Carga de los tipos de cocina desde la base de datos
        for tipo_id, nombre in datos.obtener_tipos_cocina():
            self.tipos_cocina[nombre] = tipo_id
            self.ui.daaj_cmbTipoCocina.addItem(nombre)

        # ==================================================
        # SEÑALES Y EVENTOS
        # ==================================================

        # Cambio de tipo de reserva
        self.ui.daaj_cmbTipoReserva.currentTextChanged.connect(
            self._cambiar_tipo
        )

        # Botón guardar
        self.ui.daaj_btnGuardar.clicked.connect(self._guardar)

        # Botón volver (cerrar diálogo)
        self.ui.daaj_btnVolver.clicked.connect(self.reject)

        # Campos ocultos por defecto
        self.ui.daaj_spnJornadas.setVisible(False)
        self.ui.daaj_chkHabitaciones.setVisible(False)

        # Si se edita una reserva, se cargan sus datos
        if self.es_edicion:
            self._cargar_reserva()

    # ==================================================
    # CARGAR DATOS DE UNA RESERVA EXISTENTE
    # ==================================================

    def _cargar_reserva(self):
        """
        Carga los datos de una reserva existente
        en los campos del formulario.
        """
        self.reserva_id = self.reserva["reserva_id"]

        # Datos personales
        self.ui.daaj_txtNombre.setText(self.reserva["persona"])
        self.ui.daaj_txtTelefono.setText(self.reserva["telefono"])

        # Fecha del evento
        self.ui.daaj_dateEvento.setDate(
            QDate.fromString(self.reserva["fecha"], "yyyy-MM-dd")
        )

        # Número de personas
        self.ui.daaj_spnPersonas.setValue(self.reserva["ocupacion"])

        # Selección de tipo de reserva y cocina
        self.ui.daaj_cmbTipoReserva.setCurrentText(
            self.reserva["tipo_reserva"]
        )
        self.ui.daaj_cmbTipoCocina.setCurrentText(
            self.reserva["tipo_cocina"]
        )

        # Campos específicos para congresos
        if self.reserva["tipo_reserva"] == "Congreso":
            self.ui.daaj_spnJornadas.setVisible(True)
            self.ui.daaj_chkHabitaciones.setVisible(True)
            self.ui.daaj_spnJornadas.setValue(self.reserva["jornadas"])
            self.ui.daaj_chkHabitaciones.setChecked(
                self.reserva["habitaciones"] == 1
            )

    # ==================================================
    # CAMBIO DE TIPO DE RESERVA
    # ==================================================

    def _cambiar_tipo(self, tipo):
        """
        Muestra u oculta campos según el tipo de reserva.

        :param tipo: texto del tipo de reserva seleccionado
        """
        es_congreso = tipo == "Congreso"
        self.ui.daaj_spnJornadas.setVisible(es_congreso)
        self.ui.daaj_chkHabitaciones.setVisible(es_congreso)

    # ==================================================
    # GUARDAR RESERVA
    # ==================================================

    def _guardar(self):
        """
        Valida los datos introducidos y guarda
        la reserva en la base de datos.
        """

        # Obtención de datos del formulario
        nombre = self.ui.daaj_txtNombre.text().strip()
        telefono = self.ui.daaj_txtTelefono.text().strip()
        fecha = self.ui.daaj_dateEvento.date().toString("yyyy-MM-dd")
        tipo_txt = self.ui.daaj_cmbTipoReserva.currentText()
        cocina_txt = self.ui.daaj_cmbTipoCocina.currentText()
        personas = self.ui.daaj_spnPersonas.value()

        # Datos específicos para congresos
        jornadas = (
            self.ui.daaj_spnJornadas.value()
            if tipo_txt == "Congreso"
            else 0
        )
        habitaciones = (
            1 if self.ui.daaj_chkHabitaciones.isChecked() else 0
        )

        # ==================================================
        # VALIDACIONES
        # ==================================================

        if not nombre or not telefono:
            QMessageBox.warning(self, "Aviso", "Campos obligatorios")
            return

        if not (
            telefono.isdigit()
            or (telefono.startswith("+00") and telefono[3:].isdigit())
        ):
            QMessageBox.warning(self, "Aviso", "Teléfono no válido")
            return

        if personas <= 0:
            QMessageBox.warning(self, "Aviso", "Personas incorrectas")
            return

        if tipo_txt == "Congreso" and jornadas <= 0:
            QMessageBox.warning(self, "Aviso", "Indique jornadas")
            return

        # ==================================================
        # PREPARACIÓN DE DATOS PARA LA BASE DE DATOS
        # ==================================================

        datos_reserva = (
            self.tipos_reserva[tipo_txt],
            self.id_salon,
            self.tipos_cocina[cocina_txt],
            nombre,
            telefono,
            fecha,
            personas,
            jornadas,
            habitaciones
        )

        # Inserción o actualización según el modo
        if self.es_edicion:
            ok, msg = datos.actualizar_reserva(
                self.reserva_id, datos_reserva
            )
        else:
            ok, msg = datos.insertar_reserva(datos_reserva)

        # Comprobación de errores
        if not ok:
            QMessageBox.critical(self, "Error", msg)
            return

        # Mensaje de confirmación
        QMessageBox.information(
            self, "Correcto", "Reserva guardada correctamente"
        )

        # Cierra el diálogo devolviendo aceptación
        self.accept()












