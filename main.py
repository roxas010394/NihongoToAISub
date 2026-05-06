import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QPushButton, QFileDialog, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import QThread, pyqtSignal

from core.engine import Subtitulador
from core.models import SubtitleLine

# Esta clase se encarta de que Whisper trabaje en segundo plano
class WhisperWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, video_path):
        super().__init__()
        self.video_path = video_path
        self.motor = Subtitulador(model_size="base")
    
    def run(self):
        try:
            #llamando al metodo en engine.py
            lineas = self.motor.procesar_video_completo(self.video_path)
            self.finished.emit(lineas)
        except Exception as e:
            self.error.emit(str(e))
# Clase de la ventana
class SubtGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Subt AI")
        self.resize(1000,600)
        self.init_ui()
    def init_ui(self):
        layout = QVBoxLayout()
        self.btn_cargar = QPushButton("Seleccionar Video")
        self.btn_cargar.clicked.connect(self.abrir_archivo)

        self.btn_procesar = QPushButton("Generar Subtitulos con IA")
        self.btn_procesar.clicked.connect(self.procesar_con_ia)
        self.btn_procesar.setEnabled(False)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Inicio", "Fin", "Texto"])

        layout.addWidget(self.btn_cargar)
        layout.addWidget(self.btn_procesar)
        layout.addWidget(self.tabla)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
    def abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir video", "", "Videos (*.mp4 *.mkv *.avi)")
        if ruta:
            self.video_actual = ruta
            self.btn_procesar.setEnabled(True)

    def procesar_con_ia(self):
        self.worker = WhisperWorker(self.video_actual)
        self.worker.finished.connect(self.rellenar_tabla)
        self.worker.start()
    def rellenar_tabla(self, lista_lineas):
        self.tabla.setRowCount(0)
        for i, linea in enumerate(lista_lineas):
            self.tabla.insertRow(i)
            from core.models import SubtitleLine
            self.tabla.setItem(i, 0, QTableWidgetItem(SubtitleLine.format_time(linea.start)))
            self.tabla.setItem(i, 1, QTableWidgetItem(SubtitleLine.format_time(linea.end)))
            self.tabla.setItem(i, 2, QTableWidgetItem(linea.text))
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = SubtGUI()
    ventana.show()
    sys.exit(app.exec())