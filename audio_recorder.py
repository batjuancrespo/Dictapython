# Módulo de grabación de audio
import threading
import time
import wave
import os
import tempfile
import struct
from datetime import datetime

# Buscar ffmpeg.exe en la carpeta del programa (donde está main.py)
def _setup_ffmpeg_path():
    # Buscar en varias ubicaciones posibles
    possible_paths = [
        # Misma carpeta que main.py
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ffmpeg.exe'),
        # Misma carpeta que audio_recorder.py
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ffmpeg.exe'),
        # Misma carpeta que el script principal
        os.path.join(os.getcwd(), 'ffmpeg.exe'),
        # Una carpeta 'ffmpeg' junto al ejecutable
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ffmpeg', 'ffmpeg.exe'),
    ]
    
    ffmpeg_path = None
    for path in possible_paths:
        path = os.path.normpath(path)
        if os.path.exists(path):
            ffmpeg_path = os.path.dirname(path)
            break
    
    if ffmpeg_path:
        os.environ['PATH'] = ffmpeg_path + os.pathsep + os.environ.get('PATH', '')
        print(f"FFmpeg encontrado en: {ffmpeg_path}")
    else:
        print("FFmpeg no encontrado. Asegúrate de que ffmpeg.exe esté en la carpeta del programa.")

_setup_ffmpeg_path()

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("ADVERTENCIA: PyAudio no está instalado. La grabación de audio no estará disponible.")

# Intentar importar pydub para compresión
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    print("ADVERTENCIA: pydub no está instalado. El audio no se comprimirá. Instala con: pip install pydub")

class AudioRecorder:
    def __init__(self, sample_rate=16000, channels=1, chunk_size=1024):
        self.on_audio_level = None
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.format = None
        self.audio = None
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.is_paused = False
        self.recording_thread = None
        self.start_time = None
        self.paused_time = 0
        self.on_status_change = None
        self.on_time_update = None
        self.current_file = None
        
        if PYAUDIO_AVAILABLE:
            try:
                self.audio = pyaudio.PyAudio()
                self.format = pyaudio.paInt16
            except Exception as e:
                print(f"Error inicializando PyAudio: {e}")
                self.audio = None
    
    def is_available(self):
        return PYAUDIO_AVAILABLE and self.audio is not None
    
    def start_recording(self):
        if not self.is_available():
            return False, "PyAudio no está disponible"
        
        if self.is_recording:
            return False, "Ya se está grabando"
        
        try:
            self.frames = []
            self.is_recording = True
            self.is_paused = False
            self.start_time = time.time()
            self.paused_time = 0
            
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            self.recording_thread = threading.Thread(target=self._record)
            self.recording_thread.start()
            
            # Iniciar timer para actualizar tiempo
            self.timer_thread = threading.Thread(target=self._update_timer)
            self.timer_thread.start()
            
            if self.on_status_change:
                self.on_status_change("recording")
            
            return True, "Grabación iniciada"
        except Exception as e:
            self.is_recording = False
            return False, f"Error al iniciar grabación: {str(e)}"
    
    def _record(self):
        while self.is_recording:
            if not self.is_paused:
                try:
                    data = self.stream.read(self.chunk_size, exception_on_overflow=False)
                    self.frames.append(data)
                    # Emit volume level (simple RMS-based heuristic)
                    if self.on_audio_level:
                        try:
                            import struct
                            count = len(data) // 2
                            if count > 0:
                                fmt = "<" + str(count) + "h"
                                samples = struct.unpack(fmt, data)
                                mean_square = sum((s*s) for s in samples) / count
                                rms = mean_square ** 0.5
                                vol = int(min(100, max(0, (rms / 32768) * 100)))
                                self.on_audio_level(vol)
                        except Exception:
                            pass
                except Exception as e:
                    print(f"Error leyendo audio: {e}")
                    break
            else:
                time.sleep(0.1)
    
    def _update_timer(self):
        while self.is_recording:
            if not self.is_paused and self.start_time:
                elapsed = time.time() - self.start_time - self.paused_time
                if self.on_time_update:
                    self.on_time_update(elapsed)
            time.sleep(0.5)
    
    def pause_recording(self):
        if self.is_recording and not self.is_paused:
            self.is_paused = True
            self.pause_start = time.time()
            if self.on_status_change:
                self.on_status_change("paused")
            return True, "Grabación pausada"
        return False, "No se puede pausar"
    
    def resume_recording(self):
        if self.is_recording and self.is_paused:
            self.is_paused = False
            self.paused_time += time.time() - self.pause_start
            if self.on_status_change:
                self.on_status_change("recording")
            return True, "Grabación reanudada"
        return False, "No se puede reanudar"
    
    def stop_recording(self):
        if not self.is_recording:
            return None, "No se está grabando"
        
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join(timeout=1)
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        # Guardar archivo temporal
        if self.frames:
            try:
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                self.current_file = temp_file.name
                temp_file.close()
                
                with wave.open(self.current_file, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(self.audio.get_sample_size(self.format))
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(self.frames))
                
                if self.on_status_change:
                    self.on_status_change("stopped")
                
                return self.current_file, "Grabación guardada"
            except Exception as e:
                return None, f"Error guardando audio: {str(e)}"
        
        return None, "No se grabó audio"
    
    def compress_audio(self, wav_file):
        """Comprime el audio a OGG/OPUS para reducir tamaño (como en la web original)"""
        if not PYDUB_AVAILABLE:
            return wav_file  # Devolver WAV si no hay pydub
        
        try:
            # Cargar audio WAV
            audio = AudioSegment.from_wav(wav_file)
            
            # Exportar como OGG con bitrate bajo (32 kbps como la web original)
            # OGG/OPUS es muy eficiente para voz
            compressed_file = wav_file.replace('.wav', '.ogg')
            
            # 32 kbps para voz - muy comprimido como la web
            audio.export(compressed_file, format="ogg", codec="libopus", bitrate="32k")
            
            # Verificar tamaño
            original_size = os.path.getsize(wav_file)
            compressed_size = os.path.getsize(compressed_file) if os.path.exists(compressed_file) else 0
            
            print(f"Audio: {original_size/1024/1024:.2f}MB -> {compressed_size/1024/1024:.2f}MB")
            
            # Eliminar WAV original si el comprimido es más pequeño
            if compressed_size > 0 and compressed_size < original_size:
                try:
                    os.remove(wav_file)
                except:
                    pass
                return compressed_file
            else:
                # Si no mejoró, eliminar el comprimido y devolver original
                try:
                    if os.path.exists(compressed_file):
                        os.remove(compressed_file)
                except:
                    pass
                return wav_file
            
        except Exception as e:
            print(f"Error comprimiendo audio: {e}")
            return wav_file
    
    def get_audio_data(self):
        """Devuelve los datos de audio grabados como bytes"""
        if self.frames:
            return b''.join(self.frames)
        return None
    
    def cleanup(self):
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
        
        if self.audio:
            try:
                self.audio.terminate()
            except:
                pass
    
    def __del__(self):
        self.cleanup()
