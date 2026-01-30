# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mostrar_reservas.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLabel,
    QListWidget, QListWidgetItem, QMainWindow, QPushButton,
    QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)

class Ui_DAAJ_MostrarReservas(object):
    def setupUi(self, daaj_mostrarReservas):
        if not daaj_mostrarReservas.objectName():
            daaj_mostrarReservas.setObjectName(u"daaj_mostrarReservas")
        self.daaj_centralWidget = QWidget(daaj_mostrarReservas)
        self.daaj_centralWidget.setObjectName(u"daaj_centralWidget")
        self.daaj_layoutHorizontal = QHBoxLayout(self.daaj_centralWidget)
        self.daaj_layoutHorizontal.setObjectName(u"daaj_layoutHorizontal")
        self.daaj_widgetIzquierda = QWidget(self.daaj_centralWidget)
        self.daaj_widgetIzquierda.setObjectName(u"daaj_widgetIzquierda")
        self.daaj_layoutIzquierda = QVBoxLayout(self.daaj_widgetIzquierda)
        self.daaj_layoutIzquierda.setObjectName(u"daaj_layoutIzquierda")
        self.daaj_layoutIzquierda.setContentsMargins(0, 0, 0, 0)
        self.daaj_lblSalones = QLabel(self.daaj_widgetIzquierda)
        self.daaj_lblSalones.setObjectName(u"daaj_lblSalones")

        self.daaj_layoutIzquierda.addWidget(self.daaj_lblSalones)

        self.daaj_lstSalones = QListWidget(self.daaj_widgetIzquierda)
        self.daaj_lstSalones.setObjectName(u"daaj_lstSalones")

        self.daaj_layoutIzquierda.addWidget(self.daaj_lstSalones)


        self.daaj_layoutHorizontal.addWidget(self.daaj_widgetIzquierda)

        self.daaj_widgetDerecha = QWidget(self.daaj_centralWidget)
        self.daaj_widgetDerecha.setObjectName(u"daaj_widgetDerecha")
        self.daaj_layoutDerecha = QVBoxLayout(self.daaj_widgetDerecha)
        self.daaj_layoutDerecha.setObjectName(u"daaj_layoutDerecha")
        self.daaj_layoutDerecha.setContentsMargins(0, 0, 0, 0)
        self.daaj_lblReservas = QLabel(self.daaj_widgetDerecha)
        self.daaj_lblReservas.setObjectName(u"daaj_lblReservas")

        self.daaj_layoutDerecha.addWidget(self.daaj_lblReservas)

        self.daaj_tblReservas = QTableWidget(self.daaj_widgetDerecha)
        if (self.daaj_tblReservas.columnCount() < 4):
            self.daaj_tblReservas.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.daaj_tblReservas.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.daaj_tblReservas.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.daaj_tblReservas.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.daaj_tblReservas.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.daaj_tblReservas.setObjectName(u"daaj_tblReservas")
        self.daaj_tblReservas.setColumnCount(4)
        self.daaj_tblReservas.setRowCount(0)

        self.daaj_layoutDerecha.addWidget(self.daaj_tblReservas)

        self.daaj_btnReservar = QPushButton(self.daaj_widgetDerecha)
        self.daaj_btnReservar.setObjectName(u"daaj_btnReservar")

        self.daaj_layoutDerecha.addWidget(self.daaj_btnReservar)


        self.daaj_layoutHorizontal.addWidget(self.daaj_widgetDerecha)

        daaj_mostrarReservas.setCentralWidget(self.daaj_centralWidget)

        self.retranslateUi(daaj_mostrarReservas)

        QMetaObject.connectSlotsByName(daaj_mostrarReservas)
    # setupUi

    def retranslateUi(self, daaj_mostrarReservas):
        daaj_mostrarReservas.setWindowTitle(QCoreApplication.translate("DAAJ_MostrarReservas", u"DAAJ \u00b7 Mostrar reservas", None))
        self.daaj_lblSalones.setText(QCoreApplication.translate("DAAJ_MostrarReservas", u"Salones disponibles", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblSalones.setToolTip(QCoreApplication.translate("DAAJ_MostrarReservas", u"Lista de salones disponibles", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.daaj_lstSalones.setToolTip(QCoreApplication.translate("DAAJ_MostrarReservas", u"Seleccione un sal\u00f3n para ver sus reservas", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_lblReservas.setText(QCoreApplication.translate("DAAJ_MostrarReservas", u"Reservas del sal\u00f3n", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblReservas.setToolTip(QCoreApplication.translate("DAAJ_MostrarReservas", u"Reservas asociadas al sal\u00f3n seleccionado", None))
#endif // QT_CONFIG(tooltip)
        ___qtablewidgetitem = self.daaj_tblReservas.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("DAAJ_MostrarReservas", u"Fecha", None));
        ___qtablewidgetitem1 = self.daaj_tblReservas.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("DAAJ_MostrarReservas", u"Persona", None));
        ___qtablewidgetitem2 = self.daaj_tblReservas.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("DAAJ_MostrarReservas", u"Tel\u00e9fono", None));
        ___qtablewidgetitem3 = self.daaj_tblReservas.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("DAAJ_MostrarReservas", u"Tipo de reserva", None));
#if QT_CONFIG(tooltip)
        self.daaj_tblReservas.setToolTip(QCoreApplication.translate("DAAJ_MostrarReservas", u"Listado de reservas del sal\u00f3n", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_btnReservar.setText(QCoreApplication.translate("DAAJ_MostrarReservas", u"Reservar", None))
#if QT_CONFIG(tooltip)
        self.daaj_btnReservar.setToolTip(QCoreApplication.translate("DAAJ_MostrarReservas", u"Crear o editar una reserva", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

