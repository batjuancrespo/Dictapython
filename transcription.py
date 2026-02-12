# Módulo de transcripción con múltiples proveedores (Groq + Gemini)
import base64
import os
from config import GEMINI_API_KEY, GROQ_API_KEY, GEMINI_MODELS, GROQ_MODELS

# Importar Gemini
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("ADVERTENCIA: google-generativeai no está instalado.")

# Importar Groq
try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("ADVERTENCIA: groq no está instalado. Instala con: pip install groq")


class TranscriptionService:
    def __init__(self):
        self.gemini_client = None
        self.groq_client = None
        
        # Configurar Gemini
        if GENAI_AVAILABLE and GEMINI_API_KEY:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.gemini_client = genai
                print("Gemini configurado correctamente")
            except Exception as e:
                print(f"Error configurando Gemini: {e}")
        
        # Configurar Groq
        if GROQ_AVAILABLE and GROQ_API_KEY:
            try:
                self.groq_client = groq.Groq(api_key=GROQ_API_KEY)
                print("Groq configurado correctamente")
            except Exception as e:
                print(f"Error configurando Groq: {e}")
    
    def is_groq_available(self):
        return GROQ_AVAILABLE and self.groq_client is not None and GROQ_API_KEY
    
    def is_gemini_available(self):
        return GENAI_AVAILABLE and self.gemini_client is not None and GEMINI_API_KEY
    
    def is_available(self):
        return self.is_groq_available() or self.is_gemini_available()
    
    def transcribe_audio(self, audio_file_path, on_status=None):
        """Transcribe audio usando Groq (primero) o Gemini (fallback)
        Returns: (text, compressed_file, error)
        """
        
        # Comprimir audio si es muy grande
        compressed_file = self._compress_audio(audio_file_path, on_status)
        
        # Determinar mime_type
        if compressed_file.endswith('.ogg'):
            mime_type = "audio/ogg"
        elif compressed_file.endswith('.mp3'):
            mime_type = "audio/mp3"
        else:
            mime_type = "audio/wav"
        
        # Leer archivo
        with open(compressed_file, 'rb') as f:
            audio_data = f.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Intentar Groq primero
        if self.is_groq_available():
            result, error = self._transcribe_groq(compressed_file, on_status)
            if result:
                return result, compressed_file, None
            print(f"Groq falló: {error}, intentando Gemini...")
        
        # Fallback a Gemini
        if self.is_gemini_available():
            result, error = self._transcribe_gemini(audio_base64, mime_type, on_status)
            return result, compressed_file, error
        
        return None, compressed_file, "No hay servicio de transcripción disponible. Configura GROQ_API_KEY o GEMINI_API_KEY en .env"
    
    def _transcribe_groq(self, audio_file_path, on_status=None):
        """Transcribe usando Groq (Whisper)"""
        if not self.is_groq_available():
            return None, "Groq no disponible"
        
        # Verificar que es un archivo de audio
        audio_extensions = ['.wav', '.ogg', '.mp3', '.m4a', '.webm', '.flac']
        if not any(audio_file_path.lower().endswith(ext) for ext in audio_extensions):
            return None, f"Archivo no es audio: {os.path.basename(audio_file_path)}"
        
        try:
            if on_status:
                on_status("Transcribiendo con Groq (Whisper)...")
            
            with open(audio_file_path, "rb") as file:
                transcription = self.groq_client.audio.transcriptions.create(
                    file=(audio_file_path, file.read()),
                    model=GROQ_MODELS[0],  # whisper-large-v3
                    language="es"
                )
            
            return transcription.text, None
            
        except Exception as e:
            return None, str(e)
    
    def _transcribe_gemini(self, audio_base64, mime_type, on_status=None):
        """Transcribe usando Gemini"""
        if not self.is_gemini_available():
            return None, "Gemini no disponible"
        
        try:
            if on_status:
                on_status("Transcribiendo con Gemini...")
            
            prompt = """Eres un sistema de transcripción estrictamente literal. Transcribe el audio exactamente como se dice, sin añadir puntuación. Los comandos de puntuación como "punto y aparte", "coma", "punto" deben aparecer como texto literal."""

            for model_name in GEMINI_MODELS:
                try:
                    model = self.gemini_client.GenerativeModel(model_name)
                    
                    response = model.generate_content([
                        prompt,
                        {
                            "mime_type": mime_type,
                            "data": audio_base64
                        }
                    ])
                    
                    if response and response.text:
                        return response.text, None
                        
                except Exception as e:
                    print(f"Error con modelo {model_name}: {e}")
                    continue
            
            return None, "Todos los modelos Gemini fallaron"
            
        except Exception as e:
            return None, f"Error en Gemini: {str(e)}"
    
    def _compress_audio(self, audio_file_path, on_status=None):
        """Comprime audio a OGG 32kbps (como la web original)"""
        # Si no es WAV, no comprimir
        if not audio_file_path.endswith('.wav'):
            print(f"Archivo no es WAV: {os.path.basename(audio_file_path)}")
            return audio_file_path
        
        file_size = os.path.getsize(audio_file_path)
        
        # Solo comprimir si es mayor de 1MB para optimizar
        if file_size <= 1 * 1024 * 1024:
            print(f"Audio muy pequeño ({file_size/1024/1024:.2f}MB), no comprime")
            return audio_file_path
        
        if on_status:
            on_status("Comprimiendo audio...")
        
        try:
            from pydub import AudioSegment
            
            print(f"Comprimiendo {file_size/1024/1024:.2f}MB...")
            audio = AudioSegment.from_wav(audio_file_path)
            compressed_file = audio_file_path.replace('.wav', '.ogg')
            
            # Exportar como OGG con bitrate bajo (32 kbps como la web)
            audio.export(compressed_file, format="ogg", codec="libopus", bitrate="32k")
            
            new_size = os.path.getsize(compressed_file)
            print(f"Comprimido: {file_size/1024/1024:.2f}MB -> {new_size/1024/1024:.2f}MB")
            
            return compressed_file if os.path.exists(compressed_file) else audio_file_path
            
        except Exception as e:
            print(f"Error comprimiendo: {e}")
            # Verificar ffmpeg
            ffmpeg_path = os.path.join(os.path.dirname(audio_file_path), 'ffmpeg.exe')
            if not os.path.exists(ffmpeg_path):
                print("ERROR: ffmpeg.exe no encontrado en la carpeta del programa")
            return audio_file_path
    
    def transcribe_text(self, text, on_status=None):
        """Procesa texto ya transcrito (para el Juanizador)"""
        # Primero intentar Groq (más rápido)
        if self.is_groq_available():
            pass  # Groq no tiene esta funcionalidad
        
        # Usar Gemini
        if self.is_gemini_available():
            try:
                if on_status:
                    on_status("Procesando con IA...")
                
                model = self.gemini_client.GenerativeModel(GEMINI_MODELS[0])
                response = model.generate_content(text)
                
                if response and response.text:
                    return response.text, None
                return None, "No se recibió respuesta"
                
            except Exception as e:
                return None, f"Error: {str(e)}"
        
        return None, "Servicio no disponible"
