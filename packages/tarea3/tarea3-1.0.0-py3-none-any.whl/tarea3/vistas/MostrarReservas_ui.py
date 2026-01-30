# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MostrarReservas.ui'
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
from PySide6.QtWidgets import (QApplication, QFrame, QHeaderView, QLabel,
    QListWidget, QListWidgetItem, QMainWindow, QPushButton,
    QSizePolicy, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget)
from ..img import imagenes_rc

class Ui_CZN_MostrarReservas(object):
    def setupUi(self, CZN_MostrarReservas):
        if not CZN_MostrarReservas.objectName():
            CZN_MostrarReservas.setObjectName(u"CZN_MostrarReservas")
        CZN_MostrarReservas.resize(735, 557)
        CZN_MostrarReservas.setMinimumSize(QSize(735, 557))
        CZN_MostrarReservas.setMaximumSize(QSize(735, 557))
        self.CZN_centralwidget = QWidget(CZN_MostrarReservas)
        self.CZN_centralwidget.setObjectName(u"CZN_centralwidget")
        self.verticalLayout = QVBoxLayout(self.CZN_centralwidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.CZN_frame = QFrame(self.CZN_centralwidget)
        self.CZN_frame.setObjectName(u"CZN_frame")
        font = QFont()
        font.setBold(False)
        self.CZN_frame.setFont(font)
        self.CZN_frame.setStyleSheet(u"background-color: rgb(0, 85, 127);")
        self.CZN_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.CZN_frame.setFrameShadow(QFrame.Shadow.Raised)
        self.CZN_tableWidgetReservas = QTableWidget(self.CZN_frame)
        if (self.CZN_tableWidgetReservas.columnCount() < 4):
            self.CZN_tableWidgetReservas.setColumnCount(4)
        __qtablewidgetitem = QTableWidgetItem()
        self.CZN_tableWidgetReservas.setHorizontalHeaderItem(0, __qtablewidgetitem)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.CZN_tableWidgetReservas.setHorizontalHeaderItem(1, __qtablewidgetitem1)
        __qtablewidgetitem2 = QTableWidgetItem()
        self.CZN_tableWidgetReservas.setHorizontalHeaderItem(2, __qtablewidgetitem2)
        __qtablewidgetitem3 = QTableWidgetItem()
        self.CZN_tableWidgetReservas.setHorizontalHeaderItem(3, __qtablewidgetitem3)
        self.CZN_tableWidgetReservas.setObjectName(u"CZN_tableWidgetReservas")
        self.CZN_tableWidgetReservas.setGeometry(QRect(40, 270, 651, 192))
        self.CZN_tableWidgetReservas.setStyleSheet(u" QTableWidget {\n"
"                background-color: #ffffff; /* Fondo blanco */\n"
"                border: none;\n"
"                gridline-color: #cccccc; /* L\u00edneas de la cuadr\u00edcula */\n"
"                font-size: 14px;\n"
"                border-radius: 8px;\n"
"            }\n"
"            QTableWidget::item {\n"
"                border: none;\n"
"                padding: 10px;\n"
"            }\n"
"            QTableWidget::item:selected {\n"
"                background-color: #6c63ff; /* Fondo azul p\u00farpura */\n"
"                color: #ffffff; /* Texto blanco */\n"
"            }\n"
"            QHeaderView::section {\n"
"                background-color: #00557f; /* Azul oscuro */\n"
"                color: white;\n"
"                font-weight: bold;\n"
"                padding: 6px;\n"
"               \n"
"                text-align: center;\n"
"            }\n"
"            QTableCornerButton::section {\n"
"                background-color: #00557f; /* Azul oscuro */\n"
"     "
                        "           border: 1px solid #cccccc;\n"
"            }")
        self.CZN_listWidget_salones = QListWidget(self.CZN_frame)
        self.CZN_listWidget_salones.setObjectName(u"CZN_listWidget_salones")
        self.CZN_listWidget_salones.setGeometry(QRect(40, 81, 651, 171))
        self.CZN_listWidget_salones.setStyleSheet(u"background-color: rgb(255, 255, 255);")
        self.CZN_ButtonReservar = QPushButton(self.CZN_frame)
        self.CZN_ButtonReservar.setObjectName(u"CZN_ButtonReservar")
        self.CZN_ButtonReservar.setGeometry(QRect(330, 500, 75, 24))
        self.CZN_ButtonReservar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.CZN_ButtonReservar.setStyleSheet(u"background-color: rgb(0, 155, 227);\n"
"color: #ffffff; \n"
"QPushButton#pushButtonReservar {\n"
"    background-color: #6c63ff;\n"
"    color: #ffffff; \n"
"    border-radius: 8px;\n"
"    padding: 6px 12px;\n"
"    font-weight: bold;\n"
"}\n"
"QPushButton#pushButtonReservar:hover {\n"
"    background-color: #5148c2;\n"
"    color: #ffffff; \n"
"}\n"
"")
        self.CZN_labelTitulo = QLabel(self.CZN_frame)
        self.CZN_labelTitulo.setObjectName(u"CZN_labelTitulo")
        self.CZN_labelTitulo.setGeometry(QRect(220, 30, 291, 31))
        self.CZN_labelTitulo.setStyleSheet(u"font: 20pt \"Segoe UI\";\n"
"color: rgb(255, 255, 255);")
        self.CZN_Label_logo = QLabel(self.CZN_frame)
        self.CZN_Label_logo.setObjectName(u"CZN_Label_logo")
        self.CZN_Label_logo.setGeometry(QRect(150, 20, 61, 51))
        self.CZN_Label_logo.setStyleSheet(u"border-image: url(:/logos/cartel-de-hotel.png);")
        self.label = QLabel(self.CZN_frame)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(40, 470, 261, 16))

        self.verticalLayout.addWidget(self.CZN_frame)

        CZN_MostrarReservas.setCentralWidget(self.CZN_centralwidget)

        self.retranslateUi(CZN_MostrarReservas)

        QMetaObject.connectSlotsByName(CZN_MostrarReservas)
    # setupUi

    def retranslateUi(self, CZN_MostrarReservas):
        CZN_MostrarReservas.setWindowTitle(QCoreApplication.translate("CZN_MostrarReservas", u"MainWindow", None))
        ___qtablewidgetitem = self.CZN_tableWidgetReservas.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("CZN_MostrarReservas", u"Fecha", None));
        ___qtablewidgetitem1 = self.CZN_tableWidgetReservas.horizontalHeaderItem(1)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("CZN_MostrarReservas", u"Persona", None));
        ___qtablewidgetitem2 = self.CZN_tableWidgetReservas.horizontalHeaderItem(2)
        ___qtablewidgetitem2.setText(QCoreApplication.translate("CZN_MostrarReservas", u"Telefono", None));
        ___qtablewidgetitem3 = self.CZN_tableWidgetReservas.horizontalHeaderItem(3)
        ___qtablewidgetitem3.setText(QCoreApplication.translate("CZN_MostrarReservas", u"Tipo de Reserva", None));
        self.CZN_ButtonReservar.setText(QCoreApplication.translate("CZN_MostrarReservas", u"RESERVAR", None))
        self.CZN_labelTitulo.setText(QCoreApplication.translate("CZN_MostrarReservas", u"GESTION DE RESERVAS", None))
        self.CZN_Label_logo.setText("")
        self.label.setText(QCoreApplication.translate("CZN_MostrarReservas", u"<html><head/><body><p>\u26a0\ufe0f <span style=\" color:#ffffff;\">Pulsa doble-click en el registro para editarlo.</span></p></body></html>", None))
    # retranslateUi

