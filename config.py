# Configuración de la aplicación
import os
from dotenv import load_dotenv

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

# Configuración de audio
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 1024
AUDIO_FORMAT = 'int16'
MAX_RECORDING_TIME = 12 * 60  # 12 minutos en segundos
RECORDING_WARNING_TIME = 11 * 60  # 11 minutos

# Lista de modelos Gemini a utilizar (por orden de preferencia)
GEMINI_MODELS = [
    'gemini-2.5-flash',
    'gemini-2.0-flash',
    'gemini-2.0-flash-lite'
]

# Modelos Groq (Whisper)
GROQ_MODELS = [
    'whisper-large-v3',
    'whisper-large',
    'whisper-medium',
    'whisper-small'
]

# Archivos de datos
VOCABULARY_FILE = 'vocabulario.json'

# Técnicas predefinidas
TECNICAS = {
    'Abd Art+Portal': 'Se realiza exploración abdominal tras la administración endovenosa de contraste con adquisición de imágenes en fase arterial y portal.',
    'Abd Portal': 'Se realiza exploración abdominal tras la administración endovenosa de contraste con adquisición de imágenes en fase portal.',
    'Tórax+Abd Art+Portal': 'Se realiza exploración toracoabdominal tras la administración endovenosa de contraste con adquisición de imágenes en fase arterial y portal.',
    'Abd Hernia': 'Se realiza exploración sin administración endovenosa de contraste con adquisición de imágenes en reposo y durante maniobra de Valsalva.',
    'Abd 3 Fases': 'Se realiza exploración sin y tras la administración endovenosa de contraste con adquisición de imágenes en fase arterial y portal.',
    'Eco Abd': 'Exploración ecográfica con sonda multifrecuencia.',
    'RM Hepática': 'Se realiza exploración abdominal con secuencias potenciadas en T1 en fase y fuera de fase, T2 sin y con saturación grasa, difusión y estudio dinámico tras la administración endovenosa de contraste.',
    'ColangioRM': 'Se realiza exploración abdominal con secuencias potenciadas en T1 en fase y fuera de fase, T2 sin y con saturación grasa, estudio dinámico tras la administración endovenosa de contraste completándose la valoración con cortes radiales respecto al colédoco orientados a la valoración de la via biliar.',
    'EnteroRM': 'Se realiza exploración abdominal con secuencias potenciadas en T2, difusión y estudio dinámico tras la administración endovenosa de contraste previa distensión de las asas intestinales. Exploración orientada a la valoración de asas de intestino delgado.',
    'RM Fístulas': 'Se realiza exploración pélvica con secuencias potenciadas en T2 sin y con saturación grasa y difusión.',
    'RM Neo Pelvis': 'Se realiza exploración pélvica con secuencias potenciadas en T2 sin y con saturación grasa en los tres planos del espacio, difusión y estudio dinámico tras la administración endovenosa de contraste.'
}

# Categorías anatómicas para el Juanizador
ANATOMICAL_CATEGORIES = [
    {"id": 0, "name": "Tiroides/glándula tiroidea", "normal": "Glándula tiroidea de tamaño y morfología normales, sin nódulos ni otras alteraciones radiológicas significativas."},
    {"id": 1, "name": "Estructuras mediastínicas vasculares y/o corazón", "normal": "Estructuras mediastinicas vasculares sin hallazgos morfológicos de interés."},
    {"id": 2, "name": "Adenopatías mediastínicas", "normal": "No se identifican adenopatías mediastínicas de tamaño significativo."},
    {"id": 3, "name": "Parénquima pulmonar", "normal": "En el parénquima pulmonar no existen imágenes nodulares ni aumentos de densidad sugestivos de afectación patológica."},
    {"id": 4, "name": "Derrame pleural y cambios secundarios", "normal": "No se objetiva derrame pleural."},
    {"id": 5, "name": "Hígado, porta y confluente esplenomesentérico venoso", "normal": "El hígado es de bordes lisos y densidad homogénea no identificándose lesiones ocupantes de espacio. Vena porta, esplénica y mesentérica de calibre normal, permeables."},
    {"id": 6, "name": "Vesícula y vía biliar", "normal": "Vesícula biliar normodistendida, de paredes finas, sin evidencia de litiasis en su interior. Vía biliar intra y extrahepática no dilatada."},
    {"id": 7, "name": "Páncreas", "normal": "Páncreas homogéneo y bien definido sin lesiones focales ni dilatación del ducto pancreático principal."},
    {"id": 8, "name": "Bazo, glándulas suprarrenales, riñones, vías excretoras, uréteres y vejiga urinaria", "normal": "Bazo, glándulas suprarrenales y riñones de tamaño, morfología y densidad normales, sin evidencia de lesiones focales. Vías excretoras, uréteres y vejiga urinaria sin alteraciones radiológicas significativas."},
    {"id": 9, "name": "Cámara gástrica, asas intestinales", "normal": "Cámara gástrica moderadamente distendida sin hallazgos relevantes. Asas de intestino delgado y marco cólico sin engrosamientos parietales ni cambios de calibre significativos."},
    {"id": 10, "name": "Líquido libre o adenopatías intra-abdominales", "normal": "No se observa líquido libre ni adenopatías intra-abdominales de aspecto patológico."},
    {"id": 11, "name": "Aorta y grandes vasos mesentéricos", "normal": "Aorta y grandes vasos mesentéricos de calibre normal, sin hallazgos significativos."},
    {"id": 12, "name": "Esqueleto axial", "normal": "Esqueleto axial incluido en el estudio sin lesiones focales ni anomalías morfológicas relevantes."},
    {"id": 13, "name": "Otros hallazgos", "normal": None},
    {"id": 14, "name": "Bases pulmonares incluidas en el estudio", "normal": "En las bases pulmonares incluidas en el estudio no se observan hallazgos patológicos de significación."},
    {"id": 15, "name": "Hemiabdomen superior incluido en el estudio", "normal": "En el hemiabdomen superior incluido en el estudio no se objetivan hallazgos relevantes."}
]
