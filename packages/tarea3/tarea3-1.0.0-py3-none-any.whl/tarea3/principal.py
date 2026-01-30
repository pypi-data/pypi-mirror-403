import sys
from PySide6.QtWidgets import QApplication
from tarea3.controladores.mostrarReservas import CZN_MostrarReservas

def main():
    app = QApplication(sys.argv)
    ventana = CZN_MostrarReservas()
    ventana.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
