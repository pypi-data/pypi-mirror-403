# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'menu.ui'
##
## Created by: Qt User Interface Compiler version 6.10.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QMainWindow, QMenu,
    QMenuBar, QSizePolicy, QVBoxLayout, QWidget)

class Ui_DAAJ_Menu(object):
    def setupUi(self, daaj_menu):
        if not daaj_menu.objectName():
            daaj_menu.setObjectName(u"daaj_menu")
        daaj_menu.resize(600, 400)
        self.daaj_actReservas = QAction(daaj_menu)
        self.daaj_actReservas.setObjectName(u"daaj_actReservas")
        self.daaj_actSalir = QAction(daaj_menu)
        self.daaj_actSalir.setObjectName(u"daaj_actSalir")
        self.centralwidget = QWidget(daaj_menu)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.daaj_lblLogo = QLabel(self.centralwidget)
        self.daaj_lblLogo.setObjectName(u"daaj_lblLogo")
        self.daaj_lblLogo.setMinimumSize(QSize(250, 200))
        self.daaj_lblLogo.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.daaj_lblLogo)

        self.daaj_lblTitulo = QLabel(self.centralwidget)
        self.daaj_lblTitulo.setObjectName(u"daaj_lblTitulo")
        self.daaj_lblTitulo.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.daaj_lblTitulo)

        daaj_menu.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(daaj_menu)
        self.menubar.setObjectName(u"menubar")
        self.daaj_menuAplicacion = QMenu(self.menubar)
        self.daaj_menuAplicacion.setObjectName(u"daaj_menuAplicacion")
        daaj_menu.setMenuBar(self.menubar)

        self.menubar.addAction(self.daaj_menuAplicacion.menuAction())
        self.daaj_menuAplicacion.addAction(self.daaj_actReservas)
        self.daaj_menuAplicacion.addSeparator()
        self.daaj_menuAplicacion.addAction(self.daaj_actSalir)

        self.retranslateUi(daaj_menu)

        QMetaObject.connectSlotsByName(daaj_menu)
    # setupUi

    def retranslateUi(self, daaj_menu):
        daaj_menu.setWindowTitle(QCoreApplication.translate("DAAJ_Menu", u"DAAJ \u00b7 Men\u00fa principal", None))
        self.daaj_actReservas.setText(QCoreApplication.translate("DAAJ_Menu", u"Gesti\u00f3n de reservas", None))
#if QT_CONFIG(tooltip)
        self.daaj_actReservas.setToolTip(QCoreApplication.translate("DAAJ_Menu", u"DAAJ - Abrir la gesti\u00f3n de reservas", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_actSalir.setText(QCoreApplication.translate("DAAJ_Menu", u"Salir", None))
#if QT_CONFIG(tooltip)
        self.daaj_actSalir.setToolTip(QCoreApplication.translate("DAAJ_Menu", u"DAAJ - Cerrar la aplicaci\u00f3n", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(tooltip)
        self.daaj_lblLogo.setToolTip(QCoreApplication.translate("DAAJ_Menu", u"DAAJ - Logo de la aplicaci\u00f3n", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_lblLogo.setText("")
        self.daaj_lblTitulo.setText(QCoreApplication.translate("DAAJ_Menu", u"<b>Gesti\u00f3n de reservas de salones</b>", None))
#if QT_CONFIG(tooltip)
        self.daaj_lblTitulo.setToolTip(QCoreApplication.translate("DAAJ_Menu", u"DAAJ - Aplicaci\u00f3n de gesti\u00f3n de reservas", None))
#endif // QT_CONFIG(tooltip)
        self.daaj_menuAplicacion.setTitle(QCoreApplication.translate("DAAJ_Menu", u"Aplicaci\u00f3n", None))
    # retranslateUi

