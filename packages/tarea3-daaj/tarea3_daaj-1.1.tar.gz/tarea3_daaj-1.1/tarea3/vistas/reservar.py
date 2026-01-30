# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'reservar.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDateEdit,
    QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QSizePolicy, QSpinBox,
    QVBoxLayout, QWidget)

class Ui_DAAJ_Reservar(object):
    def setupUi(self, daaj_dialogReservar):
        if not daaj_dialogReservar.objectName():
            daaj_dialogReservar.setObjectName(u"daaj_dialogReservar")
        self.daaj_layoutPrincipal = QVBoxLayout(daaj_dialogReservar)
        self.daaj_layoutPrincipal.setObjectName(u"daaj_layoutPrincipal")
        self.daaj_formLayout = QFormLayout()
        self.daaj_formLayout.setObjectName(u"daaj_formLayout")
        self.daaj_lblNombre = QLabel(daaj_dialogReservar)
        self.daaj_lblNombre.setObjectName(u"daaj_lblNombre")

        self.daaj_formLayout.setWidget(0, QFormLayout.ItemRole.LabelRole, self.daaj_lblNombre)

        self.daaj_txtNombre = QLineEdit(daaj_dialogReservar)
        self.daaj_txtNombre.setObjectName(u"daaj_txtNombre")

        self.daaj_formLayout.setWidget(0, QFormLayout.ItemRole.FieldRole, self.daaj_txtNombre)

        self.daaj_lblTelefono = QLabel(daaj_dialogReservar)
        self.daaj_lblTelefono.setObjectName(u"daaj_lblTelefono")

        self.daaj_formLayout.setWidget(1, QFormLayout.ItemRole.LabelRole, self.daaj_lblTelefono)

        self.daaj_txtTelefono = QLineEdit(daaj_dialogReservar)
        self.daaj_txtTelefono.setObjectName(u"daaj_txtTelefono")

        self.daaj_formLayout.setWidget(1, QFormLayout.ItemRole.FieldRole, self.daaj_txtTelefono)

        self.daaj_lblFecha = QLabel(daaj_dialogReservar)
        self.daaj_lblFecha.setObjectName(u"daaj_lblFecha")

        self.daaj_formLayout.setWidget(2, QFormLayout.ItemRole.LabelRole, self.daaj_lblFecha)

        self.daaj_dateEvento = QDateEdit(daaj_dialogReservar)
        self.daaj_dateEvento.setObjectName(u"daaj_dateEvento")
        self.daaj_dateEvento.setCalendarPopup(True)

        self.daaj_formLayout.setWidget(2, QFormLayout.ItemRole.FieldRole, self.daaj_dateEvento)

        self.daaj_lblTipoReserva = QLabel(daaj_dialogReservar)
        self.daaj_lblTipoReserva.setObjectName(u"daaj_lblTipoReserva")

        self.daaj_formLayout.setWidget(3, QFormLayout.ItemRole.LabelRole, self.daaj_lblTipoReserva)

        self.daaj_cmbTipoReserva = QComboBox(daaj_dialogReservar)
        self.daaj_cmbTipoReserva.setObjectName(u"daaj_cmbTipoReserva")

        self.daaj_formLayout.setWidget(3, QFormLayout.ItemRole.FieldRole, self.daaj_cmbTipoReserva)

        self.daaj_lblPersonas = QLabel(daaj_dialogReservar)
        self.daaj_lblPersonas.setObjectName(u"daaj_lblPersonas")

        self.daaj_formLayout.setWidget(4, QFormLayout.ItemRole.LabelRole, self.daaj_lblPersonas)

        self.daaj_spnPersonas = QSpinBox(daaj_dialogReservar)
        self.daaj_spnPersonas.setObjectName(u"daaj_spnPersonas")
        self.daaj_spnPersonas.setMinimum(1)

        self.daaj_formLayout.setWidget(4, QFormLayout.ItemRole.FieldRole, self.daaj_spnPersonas)

        self.daaj_lblTipoCocina = QLabel(daaj_dialogReservar)
        self.daaj_lblTipoCocina.setObjectName(u"daaj_lblTipoCocina")

        self.daaj_formLayout.setWidget(5, QFormLayout.ItemRole.LabelRole, self.daaj_lblTipoCocina)

        self.daaj_cmbTipoCocina = QComboBox(daaj_dialogReservar)
        self.daaj_cmbTipoCocina.setObjectName(u"daaj_cmbTipoCocina")

        self.daaj_formLayout.setWidget(5, QFormLayout.ItemRole.FieldRole, self.daaj_cmbTipoCocina)

        self.daaj_lblJornadas = QLabel(daaj_dialogReservar)
        self.daaj_lblJornadas.setObjectName(u"daaj_lblJornadas")

        self.daaj_formLayout.setWidget(6, QFormLayout.ItemRole.LabelRole, self.daaj_lblJornadas)

        self.daaj_spnJornadas = QSpinBox(daaj_dialogReservar)
        self.daaj_spnJornadas.setObjectName(u"daaj_spnJornadas")
        self.daaj_spnJornadas.setVisible(False)

        self.daaj_formLayout.setWidget(6, QFormLayout.ItemRole.FieldRole, self.daaj_spnJornadas)

        self.daaj_chkHabitaciones = QCheckBox(daaj_dialogReservar)
        self.daaj_chkHabitaciones.setObjectName(u"daaj_chkHabitaciones")
        self.daaj_chkHabitaciones.setVisible(False)

        self.daaj_formLayout.setWidget(7, QFormLayout.ItemRole.FieldRole, self.daaj_chkHabitaciones)


        self.daaj_layoutPrincipal.addLayout(self.daaj_formLayout)

        self.daaj_layoutBotones = QHBoxLayout()
        self.daaj_layoutBotones.setObjectName(u"daaj_layoutBotones")
        self.daaj_btnVolver = QPushButton(daaj_dialogReservar)
        self.daaj_btnVolver.setObjectName(u"daaj_btnVolver")

        self.daaj_layoutBotones.addWidget(self.daaj_btnVolver)

        self.daaj_btnGuardar = QPushButton(daaj_dialogReservar)
        self.daaj_btnGuardar.setObjectName(u"daaj_btnGuardar")

        self.daaj_layoutBotones.addWidget(self.daaj_btnGuardar)


        self.daaj_layoutPrincipal.addLayout(self.daaj_layoutBotones)


        self.retranslateUi(daaj_dialogReservar)

        QMetaObject.connectSlotsByName(daaj_dialogReservar)
    # setupUi

    def retranslateUi(self, daaj_dialogReservar):
        daaj_dialogReservar.setWindowTitle(QCoreApplication.translate("DAAJ_Reservar", u"DAAJ \u00b7 Reservar", None))
        self.daaj_lblNombre.setText(QCoreApplication.translate("DAAJ_Reservar", u"Nombre", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblNombre.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Nombre de la persona que realiza la reserva", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.daaj_txtNombre.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Introduzca el nombre del contacto", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_lblTelefono.setText(QCoreApplication.translate("DAAJ_Reservar", u"Tel\u00e9fono", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblTelefono.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Tel\u00e9fono de contacto", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.daaj_txtTelefono.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Introduzca el tel\u00e9fono de contacto", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_lblFecha.setText(QCoreApplication.translate("DAAJ_Reservar", u"Fecha del evento", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblFecha.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Fecha en la que se celebrar\u00e1 el evento", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.daaj_dateEvento.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Seleccione la fecha del evento", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_lblTipoReserva.setText(QCoreApplication.translate("DAAJ_Reservar", u"Tipo de reserva", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblTipoReserva.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Seleccione el tipo de evento", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.daaj_cmbTipoReserva.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Tipo de reserva", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_lblPersonas.setText(QCoreApplication.translate("DAAJ_Reservar", u"N\u00famero de personas", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblPersonas.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"N\u00famero de asistentes al evento", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.daaj_spnPersonas.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"N\u00famero de personas que asistir\u00e1n", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_lblTipoCocina.setText(QCoreApplication.translate("DAAJ_Reservar", u"Tipo de cocina", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblTipoCocina.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Seleccione el tipo de cocina", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.daaj_cmbTipoCocina.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Tipo de cocina para el evento", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_lblJornadas.setText(QCoreApplication.translate("DAAJ_Reservar", u"N\u00famero de jornadas", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblJornadas.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"N\u00famero de d\u00edas del congreso", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.daaj_spnJornadas.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Solo para congresos", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_chkHabitaciones.setText(QCoreApplication.translate("DAAJ_Reservar", u"Requiere habitaciones", None))
#if QT_CONFIG(tooltip)
        self.daaj_chkHabitaciones.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Indica si se necesitan habitaciones", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_btnVolver.setText(QCoreApplication.translate("DAAJ_Reservar", u"Volver", None))
#if QT_CONFIG(tooltip)
        self.daaj_btnVolver.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Cancelar y volver a la ventana anterior", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_btnGuardar.setText(QCoreApplication.translate("DAAJ_Reservar", u"Reservar", None))
#if QT_CONFIG(tooltip)
        self.daaj_btnGuardar.setToolTip(QCoreApplication.translate("DAAJ_Reservar", u"Guardar la reserva", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

