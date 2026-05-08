from .models import SubtitleLine
import whisper
import subprocess
import os
import re

class Subtitulador:
    def __init__(self, model_size="base"):
        self.lines = []
        self.model_size = model_size
        self.model = None#WhisperModel(self.model_size, device="cpu", compute_type="int8")
    def cargar_modelo(self):
        if self.model is None:
            import torch
            torch.set_num_threads(8)
            self.model = whisper.load_model(self.model_size)
    def auto_timing_whisper(self, audio_file):
        self.cargar_modelo()
        #segments, info = self.model.transcribe(audio_file, beam_size=5)
        result = self.model.transcribe(audio_file, language="ja")
        for segment in result['segments']:
            
            nueva_linea = SubtitleLine(
                start_time = segment['start'],
                end_time = segment['end'],
                text = segment['text'].strip()
                )
            self.lines.append(nueva_linea)
            print(f"[{segment['start']:.2f}s -> {segment['end']:.2f}s] {segment['text']}")
        return self.lines
    def export_ass(self, filename):
        header = [
            "[Script Info]",
            "ScriptType: v4.00+",
            "PlayResX: 1920",
            "PlayResY: 1080",
            "Timer: 100.0000",
            "",
            "[V4+ Styles]",
            "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
            "Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,10,10,10,1",
            "",
            "[Events]",
            "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"
        ]
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(header)+"\n")
            for line in self.lines:
                start = SubtitleLine.format_time(line.start)
                end = SubtitleLine.format_time(line.end)
                f.write(f"Dialogue: 0, {start}, {end}, {line.style},,0,0,0,,{line.text}\n")
        print(f"✅ Archivo exportado exitosamente: {filename}")
    def import_ass(self, filename):
        self.lines = []
        from core.models import SubtitleLine
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("Dialogue"):
                    partes = line.split(",", 9)
                    if len(partes)<10:
                        continue
                    start_str = partes[1].strip()
                    end_str = partes[2].strip()
                    texto = re.sub(r'\{.*?\}', '', partes[9].strip())
                    def ass_time_to_secs(time_str):
                        h,m,s = time_str.split(':')
                        return  int(h) * 3600 + int(m) * 60 + float(s)
                    nueva_linea = SubtitleLine(start_time = ass_time_to_secs(start_str), end_time = ass_time_to_secs(end_str), text = texto)
                    self.lines.append(nueva_linea)
        return self.lines
    def extraer_audio(self, video_path):
        #Extrae el audio de un video y lo guarda en un .wav temporal
        audio_output = "temp_audio.wav"
        print(f"Extrayendo audio de :{os.path.basename(video_path)}...")
        """
        Comando FFmpeg:
        -y: Sobreescribir si ya existe
        -i: Archivo de entrada
        -ar 16000: Frecuencia de muestreo (Whisper prefiere a 16kHz)
        -ac 1: Mono (suficiente para la transcripcion)
        """
        command = ['ffmpeg', '-y', '-i', video_path, '-ar', '16000', '-ac', '1',audio_output]
        try:
            #Ejecutamos el comando
            subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return audio_output
        except subprocess.CalledProcessError:
            print("❌ Error: Asegúrate de tener FFmpeg instalado y en el PATH del sistema.")
            return None
    def procesar_video_completo(self, video_path):
        #1.- Extraer el audio
        audio_temp = self.extraer_audio(video_path)
        if not audio_temp:
            return None
        # 2.- Pasar el audio por Whisper
        lineas_generadas = self.auto_timing_whisper(audio_temp)
        #3.-Limpieza: Borrar el archivo temporal de audio para no dejar basura
        if os.path.exists(audio_temp):
            os.remove(audio_temp)
            print("Cleaning: Archivo temporal eliminado.")
        return lineas_generadas