# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Reservar.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDateEdit, QDialog,
    QFrame, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSpinBox, QVBoxLayout, QWidget)
from ..img import imagenes_rc

class Ui_CZN_Dialog(object):
    def setupUi(self, CZN_Dialog):
        if not CZN_Dialog.objectName():
            CZN_Dialog.setObjectName(u"CZN_Dialog")
        CZN_Dialog.resize(600, 600)
        CZN_Dialog.setMinimumSize(QSize(600, 600))
        CZN_Dialog.setMaximumSize(QSize(600, 600))
        self.verticalLayout = QVBoxLayout(CZN_Dialog)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.CZN_frameFondo = QFrame(CZN_Dialog)
        self.CZN_frameFondo.setObjectName(u"CZN_frameFondo")
        self.CZN_frameFondo.setStyleSheet(u"\n"
"background-color: rgb(0, 85, 127);\n"
"      ")
        self.CZN_frameFondo.setFrameShape(QFrame.Shape.StyledPanel)
        self.CZN_frameFondo.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_2 = QVBoxLayout(self.CZN_frameFondo)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.CZN_frameContent = QFrame(self.CZN_frameFondo)
        self.CZN_frameContent.setObjectName(u"CZN_frameContent")
        self.CZN_frameContent.setCursor(QCursor(Qt.CursorShape.ArrowCursor))
        self.CZN_frameContent.setStyleSheet(u"QFrame#CZN_frameContent {\n"
"    background-color: rgb(0, 85, 127);\n"
"}\n"
"\n"
"/* Aplica a todos los QLabel dentro de frameContent */\n"
"QFrame#CZN_frameContent QLabel {\n"
"    color: white;\n"
"    font-weight: bold; \n"
"}\n"
"\n"
"/*hacer el borde redondeado para que se vea mas bonito*/\n"
"QLineEdit , \n"
"QDateEdit, \n"
"QComboBox, \n"
"QSpinBox{\n"
"    border: 2px solid #cccccc;\n"
"    border-radius: 8px;\n"
"    padding: 4px;\n"
"    background-color: white;\n"
"}\n"
"\n"
"\n"
"\n"
"")
        self.CZN_frameContent.setFrameShape(QFrame.Shape.StyledPanel)
        self.CZN_frameContent.setFrameShadow(QFrame.Shadow.Raised)
        self.CZN_labelNombre = QLabel(self.CZN_frameContent)
        self.CZN_labelNombre.setObjectName(u"CZN_labelNombre")
        self.CZN_labelNombre.setGeometry(QRect(90, 140, 61, 16))
        self.CZN_labelNombre.setStyleSheet(u"color: white;")
        self.CZN_labelTLF = QLabel(self.CZN_frameContent)
        self.CZN_labelTLF.setObjectName(u"CZN_labelTLF")
        self.CZN_labelTLF.setGeometry(QRect(90, 180, 61, 16))
        self.CZN_labelTLF.setStyleSheet(u"color: white;")
        self.CZN_labelFecha = QLabel(self.CZN_frameContent)
        self.CZN_labelFecha.setObjectName(u"CZN_labelFecha")
        self.CZN_labelFecha.setGeometry(QRect(90, 220, 101, 16))
        self.CZN_labelTipoReserva = QLabel(self.CZN_frameContent)
        self.CZN_labelTipoReserva.setObjectName(u"CZN_labelTipoReserva")
        self.CZN_labelTipoReserva.setGeometry(QRect(90, 260, 91, 16))
        self.CZN_labelNumReserva = QLabel(self.CZN_frameContent)
        self.CZN_labelNumReserva.setObjectName(u"CZN_labelNumReserva")
        self.CZN_labelNumReserva.setGeometry(QRect(90, 300, 91, 16))
        self.CZN_labelTipoCocina = QLabel(self.CZN_frameContent)
        self.CZN_labelTipoCocina.setObjectName(u"CZN_labelTipoCocina")
        self.CZN_labelTipoCocina.setGeometry(QRect(90, 340, 91, 16))
        self.CZN_lineEditNombre = QLineEdit(self.CZN_frameContent)
        self.CZN_lineEditNombre.setObjectName(u"CZN_lineEditNombre")
        self.CZN_lineEditNombre.setGeometry(QRect(240, 135, 261, 26))
        self.CZN_lineEditNombre.setStyleSheet(u"background-color: white;")
        self.CZN_lineEditTelefono = QLineEdit(self.CZN_frameContent)
        self.CZN_lineEditTelefono.setObjectName(u"CZN_lineEditTelefono")
        self.CZN_lineEditTelefono.setGeometry(QRect(240, 175, 261, 26))
        self.CZN_lineEditTelefono.setStyleSheet(u"background-color: white;")
        self.CZN_dateEditFecha = QDateEdit(self.CZN_frameContent)
        self.CZN_dateEditFecha.setObjectName(u"CZN_dateEditFecha")
        self.CZN_dateEditFecha.setGeometry(QRect(240, 215, 261, 26))
        self.CZN_dateEditFecha.setStyleSheet(u"background-color: white;")
        self.CZN_dateEditFecha.setCalendarPopup(True)
        self.CZN_comboBoxTipoReserva = QComboBox(self.CZN_frameContent)
        self.CZN_comboBoxTipoReserva.addItem("")
        self.CZN_comboBoxTipoReserva.addItem("")
        self.CZN_comboBoxTipoReserva.addItem("")
        self.CZN_comboBoxTipoReserva.setObjectName(u"CZN_comboBoxTipoReserva")
        self.CZN_comboBoxTipoReserva.setGeometry(QRect(240, 255, 261, 26))
        self.CZN_comboBoxTipoReserva.setStyleSheet(u"background-color: white;")
        self.CZN_comboBoxTipoReserva.setEditable(False)
        self.CZN_spinBoxPersonas = QSpinBox(self.CZN_frameContent)
        self.CZN_spinBoxPersonas.setObjectName(u"CZN_spinBoxPersonas")
        self.CZN_spinBoxPersonas.setGeometry(QRect(240, 295, 261, 26))
        self.CZN_spinBoxPersonas.setStyleSheet(u"background-color: white;")
        self.CZN_spinBoxPersonas.setMinimum(1)
        self.CZN_spinBoxPersonas.setMaximum(9999)
        self.CZN_comboBoxTipoCocina = QComboBox(self.CZN_frameContent)
        self.CZN_comboBoxTipoCocina.addItem("")
        self.CZN_comboBoxTipoCocina.addItem("")
        self.CZN_comboBoxTipoCocina.addItem("")
        self.CZN_comboBoxTipoCocina.addItem("")
        self.CZN_comboBoxTipoCocina.setObjectName(u"CZN_comboBoxTipoCocina")
        self.CZN_comboBoxTipoCocina.setGeometry(QRect(240, 335, 261, 26))
        self.CZN_comboBoxTipoCocina.setStyleSheet(u"background-color: white;")
        self.CZN_labelJornadas = QLabel(self.CZN_frameContent)
        self.CZN_labelJornadas.setObjectName(u"CZN_labelJornadas")
        self.CZN_labelJornadas.setGeometry(QRect(90, 380, 111, 16))
        self.CZN_spinBoxJornadas = QSpinBox(self.CZN_frameContent)
        self.CZN_spinBoxJornadas.setObjectName(u"CZN_spinBoxJornadas")
        self.CZN_spinBoxJornadas.setGeometry(QRect(240, 375, 261, 26))
        self.CZN_spinBoxJornadas.setStyleSheet(u"background-color: white;")
        self.CZN_spinBoxJornadas.setMinimum(1)
        self.CZN_spinBoxJornadas.setMaximum(30)
        self.CZN_labelHabitaciones = QLabel(self.CZN_frameContent)
        self.CZN_labelHabitaciones.setObjectName(u"CZN_labelHabitaciones")
        self.CZN_labelHabitaciones.setGeometry(QRect(90, 420, 131, 16))
        self.CZN_comboBoxHabitaciones = QComboBox(self.CZN_frameContent)
        self.CZN_comboBoxHabitaciones.addItem("")
        self.CZN_comboBoxHabitaciones.addItem("")
        self.CZN_comboBoxHabitaciones.setObjectName(u"CZN_comboBoxHabitaciones")
        self.CZN_comboBoxHabitaciones.setGeometry(QRect(240, 415, 261, 26))
        self.CZN_comboBoxHabitaciones.setStyleSheet(u"background-color: white;")
        self.CZN_ButtonVolver = QPushButton(self.CZN_frameContent)
        self.CZN_ButtonVolver.setObjectName(u"CZN_ButtonVolver")
        self.CZN_ButtonVolver.setGeometry(QRect(90, 490, 80, 30))
        self.CZN_ButtonVolver.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.CZN_ButtonVolver.setStyleSheet(u"\n"
"background-color: rgb(255, 170, 0);\n"
"color: #000000;\n"
"font-weight: bold;\n"
"border-radius: 6px;\n"
"padding: 4px 12px;\n"
"          ")
        self.CZN_ButtonReservar = QPushButton(self.CZN_frameContent)
        self.CZN_ButtonReservar.setObjectName(u"CZN_ButtonReservar")
        self.CZN_ButtonReservar.setGeometry(QRect(420, 490, 80, 30))
        self.CZN_ButtonReservar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.CZN_ButtonReservar.setStyleSheet(u"\n"
"background-color: rgb(85, 170, 255);\n"
"color: #000000;\n"
"font-weight: bold;\n"
"border-radius: 6px;\n"
"padding: 4px 12px;\n"
"          ")
        self.CZN_frameHeader = QFrame(self.CZN_frameContent)
        self.CZN_frameHeader.setObjectName(u"CZN_frameHeader")
        self.CZN_frameHeader.setGeometry(QRect(-1, 0, 601, 81))
        self.CZN_frameHeader.setStyleSheet(u"background-color: rgb(85, 170, 255);")
        self.CZN_frameHeader.setFrameShape(QFrame.Shape.StyledPanel)
        self.CZN_frameHeader.setFrameShadow(QFrame.Shadow.Raised)
        self.CZN_labelHeader = QLabel(self.CZN_frameHeader)
        self.CZN_labelHeader.setObjectName(u"CZN_labelHeader")
        self.CZN_labelHeader.setGeometry(QRect(220, 30, 181, 31))
        self.CZN_labelHeader.setStyleSheet(u"font: 28pt \"Stencil\";")
        self.label = QLabel(self.CZN_frameHeader)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(170, 20, 41, 41))
        self.label.setStyleSheet(u"border-image: url(:/logos/cita.png);")

        self.verticalLayout_2.addWidget(self.CZN_frameContent)


        self.verticalLayout.addWidget(self.CZN_frameFondo)


        self.retranslateUi(CZN_Dialog)

        QMetaObject.connectSlotsByName(CZN_Dialog)
    # setupUi

    def retranslateUi(self, CZN_Dialog):
        CZN_Dialog.setWindowTitle(QCoreApplication.translate("CZN_Dialog", u"Dialog", None))
        self.CZN_labelNombre.setText(QCoreApplication.translate("CZN_Dialog", u"Nombre:", None))
        self.CZN_labelTLF.setText(QCoreApplication.translate("CZN_Dialog", u"Tel\u00e9fono:", None))
        self.CZN_labelFecha.setText(QCoreApplication.translate("CZN_Dialog", u"Fecha del evento:", None))
        self.CZN_labelTipoReserva.setText(QCoreApplication.translate("CZN_Dialog", u"Tipo de Reserva:", None))
        self.CZN_labelNumReserva.setText(QCoreApplication.translate("CZN_Dialog", u"N\u00ba de Personas:", None))
        self.CZN_labelTipoCocina.setText(QCoreApplication.translate("CZN_Dialog", u"Tipo de cocina:", None))
        self.CZN_comboBoxTipoReserva.setItemText(0, QCoreApplication.translate("CZN_Dialog", u"Banquete", None))
        self.CZN_comboBoxTipoReserva.setItemText(1, QCoreApplication.translate("CZN_Dialog", u"Jornada", None))
        self.CZN_comboBoxTipoReserva.setItemText(2, QCoreApplication.translate("CZN_Dialog", u"Congreso", None))

        self.CZN_comboBoxTipoReserva.setPlaceholderText(QCoreApplication.translate("CZN_Dialog", u"Inserta Tipo", None))
        self.CZN_comboBoxTipoCocina.setItemText(0, QCoreApplication.translate("CZN_Dialog", u"Buf\u00e9", None))
        self.CZN_comboBoxTipoCocina.setItemText(1, QCoreApplication.translate("CZN_Dialog", u"Carta", None))
        self.CZN_comboBoxTipoCocina.setItemText(2, QCoreApplication.translate("CZN_Dialog", u"Pedir cita con el chef", None))
        self.CZN_comboBoxTipoCocina.setItemText(3, QCoreApplication.translate("CZN_Dialog", u"No precisa", None))

        self.CZN_comboBoxTipoCocina.setPlaceholderText(QCoreApplication.translate("CZN_Dialog", u"Inserta Tipo", None))
        self.CZN_labelJornadas.setText(QCoreApplication.translate("CZN_Dialog", u"N\u00ba Jornadas:", None))
        self.CZN_labelHabitaciones.setText(QCoreApplication.translate("CZN_Dialog", u"\u00bfHabitaciones?", None))
        self.CZN_comboBoxHabitaciones.setItemText(0, QCoreApplication.translate("CZN_Dialog", u"No", None))
        self.CZN_comboBoxHabitaciones.setItemText(1, QCoreApplication.translate("CZN_Dialog", u"S\u00ed", None))

        self.CZN_ButtonVolver.setText(QCoreApplication.translate("CZN_Dialog", u"Volver", None))
        self.CZN_ButtonReservar.setText(QCoreApplication.translate("CZN_Dialog", u"Reservar", None))
        self.CZN_labelHeader.setText(QCoreApplication.translate("CZN_Dialog", u"RESERVA", None))
        self.label.setText("")
    # retranslateUi

