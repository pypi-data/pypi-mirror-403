from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import QDate

from ..vistas.Reservar_ui import Ui_CZN_Dialog  
from ..controladores.conexion import (
    CZN_obtener_tipos_reserva, CZN_obtener_tipos_cocina, CZN_actualizar_reserva, CZN_CrearConexion,
    CZN_insertar_reserva, CZN_obtener_reserva, CZN_obtener_reservas_por_salon, CZN_obtener_salones
)


class ReservarDialog(QDialog, Ui_CZN_Dialog):
    """
    Diálogo para crear o editar una reserva.
    """
    
    #constructor
    def __init__(self, salon_id, reserva_id=None, parent=None):
        """
        :param salon_id: salón sobre el que se hace la reserva
        :param reserva_id: si es None se hace una nueva reserva; si no se edita
        """
        super().__init__(parent)
        self.setupUi(self)

        self.salon_id = salon_id
        self.reserva_id = reserva_id

        # listas de mapeo [(id, nombre, req_j, req_h), ...]
        self._tipos_reserva = []
        self._tipos_cocina = []

        # rellenar combos y fecha
        self.CZN_cargar_tipos()
        self.CZN_configurar_fecha()

        # eventos
        self.CZN_comboBoxTipoReserva.currentIndexChanged.connect(
            self.CZN_cambio_tipo_reserva
        )
        self.CZN_ButtonReservar.clicked.connect(self.CZN_guardar)
        self.CZN_ButtonVolver.clicked.connect(self.reject)

        # si estamos editando, cargar valores
        if self.reserva_id is not None:
            self.CZN_cargar_reserva()

        # asegurar estados iniciales
        self.CZN_cambio_tipo_reserva()


    # =================== CARGA DE DATOS UI ======================

    def CZN_cargar_tipos(self):
        """Cargar tipos de reserva y cocina desde la BD."""
        
        # Tipos de reserva
        self._tipos_reserva = CZN_obtener_tipos_reserva()
        self.CZN_comboBoxTipoReserva.clear()
        for _id, nombre, req_j, req_h in self._tipos_reserva:
            self.CZN_comboBoxTipoReserva.addItem(nombre)

        # Tipos de cocina
        self._tipos_cocina = CZN_obtener_tipos_cocina()
        self.CZN_comboBoxTipoCocina.clear()
        for _id, nombre in self._tipos_cocina:
            self.CZN_comboBoxTipoCocina.addItem(nombre)

        # Habitaciones comboBox
        self.CZN_comboBoxHabitaciones.clear()
        self.CZN_comboBoxHabitaciones.addItems(["No", "Sí"])


    def CZN_configurar_fecha(self):
        """Fecha actual por defecto."""
        self.CZN_dateEditFecha.setDate(QDate.currentDate())


    def CZN_cambio_tipo_reserva(self):
        """activa o desactiva campos según sea Banquete/Jornada/Congreso."""
        idx = self.CZN_comboBoxTipoReserva.currentIndex()
        if idx < 0:
            return

        _, _, req_j, req_h = self._tipos_reserva[idx]

        # Jornadas
        self.CZN_spinBoxJornadas.setEnabled(bool(req_j))
        if not req_j:
            self.CZN_spinBoxJornadas.setValue(0)

        # Habitaciones
        self.CZN_comboBoxHabitaciones.setEnabled(bool(req_h))
        if not req_h:
            self.CZN_comboBoxHabitaciones.setCurrentIndex(0)


    def CZN_cargar_reserva(self):
        """rellena los datos si es una edición."""
        datos = CZN_obtener_reserva(self.reserva_id)

        (rid, tipo_reserva_id, salon_id, tipo_cocina_id,
         persona, telefono, fecha, ocupacion, jornadas, habitaciones) = datos

        # nombre, teléfono, personas
        self.CZN_lineEditNombre.setText(persona)
        self.CZN_lineEditTelefono.setText(telefono)
        self.CZN_spinBoxPersonas.setValue(ocupacion)

        # fecha
        qdate = QDate.fromString(fecha, "d/M/yyyy")  # mismo formato que en la base de datos
        if qdate.isValid():
            self.CZN_dateEditFecha.setDate(qdate)

        # tipo reserva
        for i, (tid, _, _, _) in enumerate(self._tipos_reserva):
            if tid == tipo_reserva_id:
                self.CZN_comboBoxTipoReserva.setCurrentIndex(i)

        # tipo cocina
        for i, (cid, _) in enumerate(self._tipos_cocina):
            if cid == tipo_cocina_id:
                self.CZN_comboBoxTipoCocina.setCurrentIndex(i)

        # jornadas y habitaciones
        self.CZN_spinBoxJornadas.setValue(jornadas)
        self.CZN_comboBoxHabitaciones.setCurrentIndex(1 if habitaciones else 0)


    # =================== VALIDACIÓN ======================

    def CZN_validar(self):
        """Comprueba que los campos obligatorios estén completos."""
        if not self.CZN_lineEditNombre.text().strip():
            QMessageBox.warning(self, "Error", "El nombre no puede estar vacío.")
            return False
        if not self.CZN_lineEditTelefono.text().strip():
            QMessageBox.warning(self, "Error", "El teléfono no puede estar vacío.")
            return False
        if self.CZN_spinBoxPersonas.value() <= 0:
            QMessageBox.warning(self, "Error", "Debe haber al menos 1 persona.")
            return False
        return True


    # =================== RECOPILAR Y GUARDAR ======================

    def CZN_recopilar_datos(self):
        """Convierte los datos del formulario en un diccionario listo para SQL."""
        qdate = self.CZN_dateEditFecha.date()
        fecha_txt = qdate.toString("d/M/yyyy")

        idx_r = self.CZN_comboBoxTipoReserva.currentIndex()
        tipo_reserva_id, _, req_j, req_h = self._tipos_reserva[idx_r]

        idx_c = self.CZN_comboBoxTipoCocina.currentIndex()
        tipo_cocina_id, _ = self._tipos_cocina[idx_c]

        jornadas = self.CZN_spinBoxJornadas.value() if req_j else 0
        habitaciones = 1 if (req_h and self.CZN_comboBoxHabitaciones.currentIndex() == 1) else 0

        return {
            "tipo_reserva_id": tipo_reserva_id,
            "salon_id": self.salon_id,
            "tipo_cocina_id": tipo_cocina_id,
            "persona": self.CZN_lineEditNombre.text().strip(),
            "telefono": self.CZN_lineEditTelefono.text().strip(),
            "fecha": fecha_txt,
            "ocupacion": self.CZN_spinBoxPersonas.value(),
            "jornadas": jornadas,
            "habitaciones": habitaciones,
        }


    def CZN_guardar(self):
        """Intento guardar los datos en la BD"""
        if not self.CZN_validar():
            return

        datos = self.CZN_recopilar_datos()
        ok = None

        if self.reserva_id is None:
            ok = CZN_insertar_reserva(datos)
        else:
            ok = CZN_actualizar_reserva(self.reserva_id, datos)

        if ok is True:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo guardar la reserva.\n\nDetalle: {ok}")
