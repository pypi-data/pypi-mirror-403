from PySide6.QtWidgets import QMainWindow, QTableWidgetItem, QMessageBox, QAbstractItemView
from PySide6.QtCore import Qt

from ..vistas.MostrarReservas_ui import Ui_CZN_MostrarReservas
from ..controladores.conexion import CZN_obtener_salones, CZN_obtener_reservas_por_salon
from ..controladores.reservar import ReservarDialog


class CZN_MostrarReservas(QMainWindow, Ui_CZN_MostrarReservas):
    """
    Clase que gestiona la ventana principal para mostrar y gestionar reservas de salones.
    """

    # constructor de la clase
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        # listas internas para saber qué id tiene cada fila
        self._salones = []     
        self._reservas = []     

        # configuración inicial de la tabla
        self.CZN_configurar_tabla()

        # conectar señales
        self.CZN_listWidget_salones.currentRowChanged.connect(self.CZN_cambio_salon)
        self.CZN_ButtonReservar.clicked.connect(self.CZN_nueva_reserva)    
        self.CZN_tableWidgetReservas.cellDoubleClicked.connect(self.CZN_doble_click_reserva)
            
        # cargar datos iniciales
        self.CZN_cargar_salones()

    # =================== CONFIGURACIÓN DE LA TABLA ===================

    # metodo para configurar la tabla
    def CZN_configurar_tabla(self):
        self.CZN_tableWidgetReservas.setColumnCount(4)
        self.CZN_tableWidgetReservas.setHorizontalHeaderLabels(
            ["Fecha", "Persona", "Teléfono", "Tipo de reserva"]
        )

        # aquí me daba un error, pero importe QAbstractitemview y ya me dejo:
        self.CZN_tableWidgetReservas.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.CZN_tableWidgetReservas.setSelectionBehavior( QAbstractItemView.SelectRows)
        self.CZN_tableWidgetReservas.horizontalHeader().setStretchLastSection(True)


    # =================== SALONES ===================

    # metodo para cargar los salones
    def CZN_cargar_salones(self):
        self._salones = CZN_obtener_salones()  
        self.CZN_listWidget_salones.clear()

        for salon_id, nombre in self._salones:
            self.CZN_listWidget_salones.addItem(nombre)


    # metodo para obtener id de un salon 
    def CZN_get_salon_actual_id(self):
        fila = self.CZN_listWidget_salones.currentRow()
        if fila < 0 or fila >= len(self._salones):
            return None
        salon_id, _ = self._salones[fila]
        return salon_id
    
    
    # metodo para detectar cuándo el usuario selecciona otro salón para cambiar las reservas
    def CZN_cambio_salon(self, fila):
        if fila < 0:
            return
        self.CZN_cargar_reservas()

    # =================== RESERVAS ===================

    # carga las reservas del salón seleccionado en la tabla.
    def CZN_cargar_reservas(self):
        salon_id = self.CZN_get_salon_actual_id()
        if salon_id is None:
            return

        # usamos la función de conexion.py para poder obtener las reservas por id salon
        self._reservas = CZN_obtener_reservas_por_salon(salon_id) 
        

        self.CZN_tableWidgetReservas.setRowCount(0)

        for fila, (reserva_id, fecha, persona, telefono, tipo) in enumerate(self._reservas):
            self.CZN_tableWidgetReservas.insertRow(fila)

            item_fecha = QTableWidgetItem(str(fecha))
            # guardamos el id de la reserva en los "user data" del item
            item_fecha.setData(Qt.UserRole, reserva_id)

            self.CZN_tableWidgetReservas.setItem(fila, 0, item_fecha)
            self.CZN_tableWidgetReservas.setItem(fila, 1, QTableWidgetItem(persona))
            self.CZN_tableWidgetReservas.setItem(fila, 2, QTableWidgetItem(telefono))
            self.CZN_tableWidgetReservas.setItem(fila, 3, QTableWidgetItem(tipo))

    # =================== ABRIR DIÁLOGO RESERVAR ===================

    # metodo para crear una nueva reserva
    def CZN_nueva_reserva(self):
        salon_id = self.CZN_get_salon_actual_id()
        if salon_id is None:
            QMessageBox.warning(self, "Aviso", "Debes seleccionar un salón.")
            return

        dlg = ReservarDialog(salon_id=salon_id, parent=self)
        if dlg.exec():     
            self.CZN_cargar_reservas()

    # metodo para editar una reserva dando doble click al registro
    def CZN_doble_click_reserva(self, fila, columna):
        salon_id = self.CZN_get_salon_actual_id()
        if salon_id is None:
            return

        item_fecha = self.CZN_tableWidgetReservas.item(fila, 0)
        if item_fecha is None:
            return

        reserva_id = item_fecha.data(Qt.UserRole)
        if reserva_id is None:
            return

        dlg = ReservarDialog(salon_id=salon_id,reserva_id=reserva_id,parent=self)

        if dlg.exec():
            self.CZN_cargar_reservas()
