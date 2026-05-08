import sys
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtMultimediaWidgets import QVideoWidget
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, QTableWidget, QPushButton, QFileDialog, QTableWidgetItem, QHeaderView, QLabel, QSlider)
from PyQt6.QtCore import QThread, pyqtSignal, QUrl, Qt

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

        self.btn_exportar = QPushButton("Exportar")
        self.btn_exportar.clicked.connect(self.guardar)
        self.btn_exportar.setEnabled(False)

        self.btn_importar = QPushButton("Importar")
        self.btn_importar.clicked.connect(self.abrir_ass)

        #----------------- SECCION DE VIDEO -----------
        self.video_container = QWidget()
        self.video_container.setMinimumHeight(400)
        video_layout = QVBoxLayout(self.video_container)

        #El widget donde se ve el video
        self.video_widget = QVideoWidget()
        #El cerebro del reproductor
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        self.media_player.setVideoOutput(self.video_widget)
        # Overlay de subtitulos
        self.lbl_subtitulo = QLabel(self.video_container)
        self.lbl_subtitulo.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.lbl_subtitulo.raise_()
        
        self.lbl_subtitulo.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180); 
            color: white; 
            border-radius: 5px;
            padding: 5px;
        """)
        self.lbl_subtitulo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_subtitulo.hide()
        self.lbl_subtitulo.setText("Subtitulos aqui")
        self.lbl_subtitulo.setFixedWidth(1000)
        self.lbl_subtitulo.move(0, 350)

        self.slider_tiempo = QSlider(Qt.Orientation.Horizontal)
        self.slider_tiempo.setRange(0,0)
        self.slider_tiempo.sliderMoved.connect(self.set_posicion_video)
        self.media_player.durationChanged.connect(self.actualizar_duracion)
        self.media_player.positionChanged.connect(self.actualizar_posicion_slider)

        video_layout.addWidget(self.video_widget)

        #Controles de reproduccion
        

        video_layout.addWidget(self.slider_tiempo)

        self.btn_play = QPushButton("Play / Pause")
        self.btn_play.clicked.connect(self.play_video)
        video_layout.addWidget(self.btn_play)

        
        



        self.tabla = QTableWidget()
        self.tabla.setColumnCount(3)
        self.tabla.setHorizontalHeaderLabels(["Inicio", "Fin", "Texto"])


        layout.addWidget(self.btn_cargar)
        layout.addWidget(self.btn_procesar)
        layout.addWidget(self.btn_exportar)
        layout.addWidget(self.btn_importar)
        layout.addWidget(self.video_container)
        layout.addWidget(self.tabla)
        

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.setStyleSheet("""
    QMainWindow, QWidget {
        background-color: #000000;
        color: #FFFFFF; /* Texto blanco para que no se pierda */
    }
    QTableWidget {
        background-color: #1E1E1E; /* Gris oscuro para la tabla */
        gridline-color: #333333;
        color: white;
    }
    QPushButton {
        background-color: #333333;
        border: 1px solid #555555;
        padding: 5px;
    }
""")
        #Conexion de sincronizacion
        self.media_player.positionChanged.connect(self.sincronizar_subtitulos)
    def actualizar_duracion(self, duracion_ms):
        self.slider_tiempo.setRange(0, duracion_ms)
    def actualizar_posicion_slider(self, posicion_ms):
        self.slider_tiempo.setValue(posicion_ms)
    def set_posicion_video(self, posicion_ms):
        self.media_player.setPosition(posicion_ms)
    def play_video(self):
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()
    def resizeEvent(self, event):
        ancho_cont = self.video_container.width()
        alto_cont = self.video_container.height()

        ancho_sub = int(ancho_cont * 0.8)
        alto_sub = 60



        self.lbl_subtitulo.setFixedSize(ancho_sub, alto_sub)

        x = int((ancho_cont - ancho_sub) / 2)
        y = alto_cont - 100
        self.lbl_subtitulo.move(x, y)

    def abrir_archivo(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Abrir video", "", "Videos (*.mp4 *.mkv *.avi)")
        if ruta:
            self.video_actual = ruta
            self.media_player.setSource(QUrl.fromLocalFile(ruta))
            self.btn_procesar.setEnabled(True)
            print(f"Video cargado: {ruta}")
    def sincronizar_subtitulos(self, posicion_ms):
        segundos_actuales = posicion_ms / 1000.0

        for i in range(self.tabla.rowCount()):
            try:
                linea = self.lineas_actuales[i]
                if linea.start <= segundos_actuales <= linea.end:
                    print(linea.text)
                    self.lbl_subtitulo.setText(linea.text)
                    self.lbl_subtitulo.show()
                    self.lbl_subtitulo.raise_()
                    return
            except Exception as e:
                print(f"Error: {e}")
                continue
        self.lbl_subtitulo.hide()
    def abrir_ass(self):
        ruta, _ = QFileDialog.getOpenFileName(self, "Importar subtitulos", "", "Substation Alpha (*.ass)")
        if ruta:
            from core.engine import Subtitulador
            motor_temp = Subtitulador()
            self.lineas_actuales = motor_temp.import_ass(ruta)
            self.rellenar_tabla(self.lineas_actuales)
            print(f"Se han importado {len(self.lineas_actuales)} lineas.")

    def procesar_con_ia(self):

        self.btn_procesar.setEnabled(False)
        self.btn_procesar.setText("Procesando... 🤖")
        self.worker = WhisperWorker(self.video_actual)
        self.worker.finished.connect(self.rellenar_tabla)
        self.worker.error.connect(self.manejar_error)
        print("Iniciando hilo")
        self.worker.start()
    def rellenar_tabla(self, lista_lineas):
        self.lineas_actuales = lista_lineas
        print(f"Recibidas {len(lista_lineas)} líneas en la interfaz")
        self.btn_procesar.setText("¡Completado! ✅")
    
        self.tabla.setRowCount(0)

        for i, linea in enumerate(lista_lineas):
            self.tabla.insertRow(i)
            from core.models import SubtitleLine
            self.tabla.setItem(i, 0, QTableWidgetItem(SubtitleLine.format_time(linea.start)))
            self.tabla.setItem(i, 1, QTableWidgetItem(SubtitleLine.format_time(linea.end)))
            self.tabla.setItem(i, 2, QTableWidgetItem(linea.text))
        self.btn_exportar.setEnabled(True)
    def manejar_error(self, error_msg):
        print(f"⚠️ ERROR EN EL HILO: {error_msg}")
        self.btn_procesar.setEnabled(True)
        self.btn_procesar.setText("Generar Subtítulos con IA")
    def guardar(self):
        ruta, _ = QFileDialog.getSaveFileName(self, "Guardar Subtítulos", "", "Substation Alpha (*.ass)")
        if ruta:
            # Llamamos a la función que encontraste en el motor
            self.worker.motor.export_ass(ruta) 
            print("¡Archivo ASS exportado con éxito!")
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ventana = SubtGUI()
    ventana.show()
    sys.exit(app.exec())