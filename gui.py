# Interfaz gráfica de la aplicación - VERSIÓN ESTILIZADA
import tkinter as tk
import time
import math
import os
import random
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import os
import platform

from audio_recorder import AudioRecorder
from transcription import TranscriptionService
from text_processor import TextProcessor
from vocabulary import VocabularyManager
from juanizador import JuanizadorService
from config import TECNICAS, MAX_RECORDING_TIME, RECORDING_WARNING_TIME

# Colores del tema oscuro de la web
COLORS = {
    'bg_primary': '#22272e',
    'bg_secondary': '#2d333b',
    'text_primary': '#adbac7',
    'text_secondary': '#768390',
    'border': '#444c56',
    'border_light': '#373e47',
    'accent': '#539bf5',
    'btn_record': '#377ef0',
    'btn_record_hover': '#539bf5',
    'btn_pause': '#d9971a',
    'btn_pause_text': '#22272e',
    'btn_stop': '#e5534b',
    'btn_stop_hover': '#f47067',
    'btn_retry': '#4387d9',
    'btn_copy': '#d9971a',
    'btn_reset': '#8957e5',
    'btn_juanizar': '#218ca3',
    'btn_success': '#28a745',
    'success': '#a3cfbb',
    'error': '#f1b0b7',
    'processing': '#b8d4fe',
    'idle': '#ced4da'
}

class StyledButton(tk.Button):
    """Botón estilizado"""
    def __init__(self, parent, text, command, bg_color, fg_color='white', 
                 hover_color=None, font_size=12, height=2, **kwargs):
        self.bg_color = bg_color
        self.hover_color = hover_color or bg_color
        self.fg_color = fg_color
        
        super().__init__(parent, text=text, command=command,
                        bg=bg_color, fg=fg_color,
                        font=('Segoe UI', font_size, 'bold'),
                        relief=tk.FLAT, borderwidth=0,
                        cursor='hand2', height=height,
                        activebackground=hover_color or bg_color,
                        activeforeground=fg_color,
                        **kwargs)
        
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def on_enter(self, event):
        self.config(bg=self.hover_color)
    
    def on_leave(self, event):
        self.config(bg=self.bg_color)

class DictadoRadiologicoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dictado Radiológico IA - by JCP")
        
        # MAXIMIZAR VENTANA
        self.root.state('zoomed')  # Windows
        # Para Linux/Mac: self.root.attributes('-zoomed', True)
        
        # Configurar tema oscuro
        self.setup_theme()
        
        # Servicios
        self.recorder = AudioRecorder()
        self.transcription = TranscriptionService()
        self.text_processor = TextProcessor()
        self.vocabulary = VocabularyManager()
        self.juanizador = JuanizadorService()
        
        # Estado
        self.current_audio_file = None
        self.compressed_audio_file = None  # Archivo comprimido (OGG)
        self.is_processing = False
        
        # Configurar callbacks del recorder
        self.recorder.on_status_change = self.on_recording_status_change
        self.recorder.on_time_update = self.on_recording_time_update
        self.volume_bar = None
        # Simulación de volumen (para pruebas cuando no hay micrófono)
        self.sim_vol_running = False
        
        self.image_refs = []
        # Nota: no activar la sección de Batman por defecto para ahorrar espacio. El usuario podrá abrirla via visual.
        
        # Importar frases desde archivo externo
        try:
            from quotes import QUOTES
            self.quotes = QUOTES
        except ImportError:
            # Frases por defecto si no existe el archivo
            self.quotes = [
                ("La medicina es la única profesión que trabaja día y noche para hacerse superflua.", "Karl Popper"),
                ("Donde hay amor por la medicina, hay amor por la humanidad.", "Hipócrates"),
                ("El diagnóstico es el arte de distinguir lo mismo de lo similar.", "Anónimo"),
                ("La mejor medicina es la que enseña al paciente a prescindir del médico.", "Thomas Edison"),
                ("El médico debe distinguir entre lo posible y lo imposible; en lo posible debe persistir.", "Paracelso"),
            ]
        self.current_quote_index = 0
        self.quote_label = None
        self.quote_author_label = None
        
        # Variables para rotación de imágenes de Batman
        self.batman_images = []  # Lista de tuplas (photo, path)
        self.batman_label = None
        self.current_batman_index = 0
        
        self.setup_ui()
        self.check_services()
        
        # Conectar callback de volumen DESPUÉS de crear la UI
        if hasattr(self.recorder, 'on_audio_level'):
            self.recorder.on_audio_level = self._on_audio_level
        
        # Iniciar rotación de frases
        self._start_quotes_rotation()
        
        # Iniciar rotación de imágenes de Batman (si hay imágenes)
        if self.batman_images:
            self._start_batman_rotation()
        
        # Atajo de teclado: Shift+Ctrl (como la web original) para empezar/detener dictamen
        self.root.bind('<Shift-Control_L>', lambda e: self.toggle_recording())
        self.root.bind('<Shift-Control_R>', lambda e: self.toggle_recording())
        # Alternativa: Ctrl+Shift (ambas órdenes cubren los casos)
        self.root.bind('<Control-Shift_L>', lambda e: self.toggle_recording())
        self.root.bind('<Control-Shift_R>', lambda e: self.toggle_recording())
    
    def setup_theme(self):
        """Configura el tema oscuro global"""
        self.root.configure(bg=COLORS['bg_primary'])
        
        # Configurar estilo ttk
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configurar colores generales
        style.configure('.',
                       background=COLORS['bg_primary'],
                       foreground=COLORS['text_primary'],
                       fieldbackground=COLORS['bg_secondary'],
                       troughcolor=COLORS['bg_secondary'])
        
        # Frames
        style.configure('TFrame', background=COLORS['bg_primary'])
        style.configure('TLabelframe', 
                       background=COLORS['bg_secondary'],
                       foreground=COLORS['text_primary'],
                       borderwidth=1,
                       relief='solid')
        style.configure('TLabelframe.Label',
                       background=COLORS['bg_secondary'],
                       foreground=COLORS['text_primary'],
                       font=('Segoe UI', 14, 'bold'))
        
        # Labels
        style.configure('TLabel',
                       background=COLORS['bg_primary'],
                       foreground=COLORS['text_primary'],
                       font=('Segoe UI', 11))
        
        # ScrolledText style
        self.text_font = ('Segoe UI', 13)  # Fuente consistente para ambos cuadros
    
    def setup_ui(self):
        """Configura la interfaz de usuario estilizada"""
        # Frame principal
        self.main_frame = tk.Frame(self.root, bg=COLORS['bg_primary'], padx=20, pady=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid responsive
        self.main_frame.columnconfigure(0, weight=3)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(2, weight=1)
        
        # ==================== TÍTULO ====================
        title_frame = tk.Frame(self.main_frame, bg=COLORS['bg_secondary'], 
                              highlightbackground=COLORS['border'],
                              highlightthickness=1, padx=30, pady=20)
        title_frame.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 20))
        title_frame.columnconfigure(1, weight=1)  # La columna de frases se expande
        
        # Frame izquierdo para el título
        title_left = tk.Frame(title_frame, bg=COLORS['bg_secondary'])
        title_left.grid(row=0, column=0, sticky='w')
        
        title_label = tk.Label(title_left, 
                              text="Dictado Radiológico ",
                              bg=COLORS['bg_secondary'],
                              fg=COLORS['text_primary'],
                              font=('Segoe UI', 28, 'bold'))
        title_label.pack(side=tk.LEFT)
        
        subtitle_label = tk.Label(title_left,
                                 text="(by JCP)",
                                 bg=COLORS['bg_secondary'],
                                 fg=COLORS['text_secondary'],
                                 font=('Segoe UI', 16))
        subtitle_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Frame derecho para las frases célebres (más espacio)
        quotes_frame_title = tk.Frame(title_frame, bg=COLORS['bg_secondary'])
        quotes_frame_title.grid(row=0, column=1, sticky='e', padx=(40, 0))
        
        # Label para la frase (con más ancho disponible)
        self.quote_label = tk.Label(quotes_frame_title,
                                   text=self.quotes[0][0] if self.quotes else "",
                                   bg=COLORS['bg_secondary'],
                                   fg=COLORS['text_primary'],
                                   font=('Segoe UI', 13, 'italic'),
                                   wraplength=600,  # Más ancho para frases largas
                                   justify=tk.RIGHT)
        self.quote_label.pack(anchor='e')
        
        # Label para el autor
        self.quote_author_label = tk.Label(quotes_frame_title,
                                          text=f"— {self.quotes[0][1]}" if self.quotes else "",
                                          bg=COLORS['bg_secondary'],
                                          fg=COLORS['text_secondary'],
                                          font=('Segoe UI', 10),
                                          justify=tk.RIGHT)
        self.quote_author_label.pack(anchor='e')
        
        # ==================== PANEL DE CONTROLES ====================
        controls_frame = tk.LabelFrame(self.main_frame, text=" Controles ",
                                      bg=COLORS['bg_secondary'],
                                      fg=COLORS['text_primary'],
                                      font=('Segoe UI', 14, 'bold'),
                                      padx=15, pady=15)
        controls_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 20))
        
        # Frame para botones
        buttons_frame = tk.Frame(controls_frame, bg=COLORS['bg_secondary'])
        buttons_frame.pack(fill=tk.X)
        
        # Botones principales
        self.record_btn = StyledButton(buttons_frame, "▶ Empezar Dictado",
                                      self.toggle_recording,
                                      COLORS['btn_record'],
                                      hover_color=COLORS['btn_record_hover'],
                                      font_size=13, width=18)
        self.record_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = StyledButton(buttons_frame, "⏸ Pausar",
                                     self.toggle_pause,
                                     COLORS['btn_pause'],
                                     fg_color=COLORS['btn_pause_text'],
                                     hover_color='#f0b72f',
                                     font_size=13, width=12)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.retry_btn = StyledButton(buttons_frame, "🔄 Reenviar audio",
                                     self.retry_processing,
                                     COLORS['btn_retry'],
                                     hover_color=COLORS['btn_record_hover'],
                                     font_size=13, width=16)
        self.retry_btn.pack(side=tk.LEFT, padx=5)
        
        separator1 = tk.Frame(buttons_frame, bg=COLORS['border'], width=2)
        separator1.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.copy_btn = StyledButton(buttons_frame, "📋 Copiar Todo",
                                    self.copy_full_report,
                                    COLORS['btn_copy'],
                                    fg_color=COLORS['btn_pause_text'],
                                    hover_color='#f0b72f',
                                    font_size=13, width=14)
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        
        self.reset_btn = StyledButton(buttons_frame, "💣 Resetear",
                                     self.reset_report,
                                     COLORS['btn_reset'],
                                     hover_color='#9b72f5',
                                     font_size=13, width=12)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        self.upload_btn = StyledButton(buttons_frame, "⬆ Subir Audio",
                                      self.upload_audio,
                                      COLORS['btn_reset'],
                                      hover_color='#9b72f5',
                                      font_size=13, width=13)
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        
        separator2 = tk.Frame(buttons_frame, bg=COLORS['border'], width=2)
        separator2.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        self.juanizar_btn = StyledButton(buttons_frame, "💡 Juanizar",
                                        self.open_juanizador,
                                        COLORS['btn_juanizar'],
                                        hover_color='#28a9c2',
                                        font_size=13, width=12)
        self.juanizar_btn.pack(side=tk.LEFT, padx=5)
        
        self.vocab_btn = StyledButton(buttons_frame, "📚 Vocabulario",
                                     self.open_vocabulary_manager,
                                     COLORS['btn_success'],
                                     hover_color='#218838',
                                     font_size=13, width=14)
        self.vocab_btn.pack(side=tk.LEFT, padx=5)
        
        # Estado y tiempo
        status_frame = tk.Frame(controls_frame, bg=COLORS['bg_secondary'], pady=10)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(status_frame, text="Listo",
                                    bg=COLORS['bg_secondary'],
                                    fg=COLORS['idle'],
                                    font=('Segoe UI', 12))
        self.status_label.pack(side=tk.LEFT)
        
        self.time_label = tk.Label(status_frame, text="",
                                  bg=COLORS['bg_secondary'],
                                  fg=COLORS['text_primary'],
                                  font=('Segoe UI', 14, 'bold'))
        self.time_label.pack(side=tk.RIGHT)

        # Medidor de volumen (sensor de audio) con indicador LED
        self.volume_frame = tk.Frame(controls_frame, bg=COLORS['bg_secondary'])
        self.volume_frame.pack(fill=tk.X, pady=(6,0))
        
        # Indicador LED de estado del micrófono
        self.mic_led = tk.Canvas(self.volume_frame, width=20, height=20, bg=COLORS['bg_secondary'], highlightthickness=0)
        self.mic_led.pack(side=tk.LEFT, padx=(8,4))
        self._draw_led('gray')  # LED gris por defecto (inactivo)
        
        vol_label = tk.Label(self.volume_frame, text="Mic:", bg=COLORS['bg_secondary'], fg=COLORS['text_primary'], font=('Segoe UI', 11, 'bold'))
        vol_label.pack(side=tk.LEFT, padx=(4,6))
        
        self.volume_bar = ttk.Progressbar(self.volume_frame, orient='horizontal', length=200, mode='determinate', maximum=100)
        self.volume_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,8))
        
        # ==================== PANEL IZQUIERDO (TEXTOS) ====================
        left_frame = tk.Frame(self.main_frame, bg=COLORS['bg_primary'])
        left_frame.grid(row=2, column=0, sticky='nsew', padx=(0, 20))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(1, weight=1)
        left_frame.rowconfigure(3, weight=3)
        
        # Técnica - AHORA CON LA MISMA FUENTE QUE EL INFORME
        tecnica_label = tk.Label(left_frame, text="Técnica Aplicada:",
                                bg=COLORS['bg_primary'],
                                fg=COLORS['text_primary'],
                                font=('Segoe UI', 14, 'bold'))
        tecnica_label.grid(row=0, column=0, sticky='w', pady=(0, 8))
        
        self.tecnica_text = tk.Text(left_frame, height=4, wrap=tk.WORD,
                                   font=self.text_font,  # MISMA FUENTE
                                   bg=COLORS['bg_secondary'],
                                   fg=COLORS['text_primary'],
                                   insertbackground=COLORS['text_primary'],
                                   relief=tk.FLAT,
                                   highlightbackground=COLORS['border'],
                                   highlightthickness=1,
                                   padx=12, pady=12)
        self.tecnica_text.grid(row=1, column=0, sticky='nsew', pady=(0, 15))
        
        # Scrollbar para técnica
        tecnica_scroll = tk.Scrollbar(left_frame, orient='vertical',
                                     command=self.tecnica_text.yview,
                                     bg=COLORS['bg_secondary'],
                                     troughcolor=COLORS['bg_primary'])
        tecnica_scroll.grid(row=1, column=1, sticky='ns', pady=(0, 15))
        self.tecnica_text.config(yscrollcommand=tecnica_scroll.set)
        
        # Informe
        informe_label = tk.Label(left_frame, text="Informe:",
                                bg=COLORS['bg_primary'],
                                fg=COLORS['text_primary'],
                                font=('Segoe UI', 14, 'bold'))
        informe_label.grid(row=2, column=0, sticky='w', pady=(0, 8))
        
        self.informe_text = tk.Text(left_frame, wrap=tk.WORD,
                                   font=self.text_font,  # MISMA FUENTE
                                   bg=COLORS['bg_secondary'],
                                   fg=COLORS['text_primary'],
                                   insertbackground=COLORS['text_primary'],
                                   relief=tk.FLAT,
                                   highlightbackground=COLORS['border'],
                                   highlightthickness=1,
                                   padx=12, pady=12)
        self.informe_text.grid(row=3, column=0, sticky='nsew')
        
        # Scrollbar para informe
        informe_scroll = tk.Scrollbar(left_frame, orient='vertical',
                                     command=self.informe_text.yview,
                                     bg=COLORS['bg_secondary'],
                                     troughcolor=COLORS['bg_primary'])
        informe_scroll.grid(row=3, column=1, sticky='ns')
        self.informe_text.config(yscrollcommand=informe_scroll.set)
        
        # ==================== PANEL DERECHO (TÉCNICAS) ====================
        right_frame = tk.LabelFrame(self.main_frame, text=" Seleccionar Técnica ",
                                   bg=COLORS['bg_secondary'],
                                   fg=COLORS['text_primary'],
                                   font=('Segoe UI', 14, 'bold'),
                                   padx=15, pady=15)
        right_frame.grid(row=2, column=1, sticky='nsew')
        right_frame.columnconfigure(0, weight=1)
        
        # Botones de técnica con colores de la web - GRID COMPACTO
        tecnica_colors = {
            'Abd Art+Portal': ('#e5534b', '#f47067'),  # Rojo
            'Abd Portal': ('#e5534b', '#f47067'),
            'Tórax+Abd Art+Portal': ('#e5534b', '#f47067'),
            'Abd Hernia': ('#e5534b', '#f47067'),
            'Abd 3 Fases': ('#e5534b', '#f47067'),
            'Eco Abd': ('#377ef0', '#539bf5'),  # Azul
            'RM Hepática': ('#d9971a', '#f0b72f'),  # Amarillo
            'ColangioRM': ('#d9971a', '#f0b72f'),
            'EnteroRM': ('#d9971a', '#f0b72f'),
            'RM Fístulas': ('#d9971a', '#f0b72f'),
            'RM Neo Pelvis': ('#d9971a', '#f0b72f'),
        }
        
        # Grid de 3 columnas, botones compactos
        COLS = 3
        for idx, (nombre, texto) in enumerate(TECNICAS.items()):
            colors = tecnica_colors.get(nombre, ('#8957e5', '#9b72f5'))
            btn = StyledButton(right_frame, nombre,
                              lambda t=texto: self.set_tecnica(t),
                              colors[0], hover_color=colors[1],
                              font_size=10, width=14, height=1)
            btn.grid(row=idx // COLS, column=idx % COLS, padx=3, pady=3, sticky='ew')
        
        for c in range(COLS):
            right_frame.columnconfigure(c, weight=1)
        
        # Botón borrar técnica - fila nueva
        row = (len(TECNICAS) + COLS - 1) // COLS
        borrar_btn = StyledButton(right_frame, "Borrar Técnica",
                                 lambda: self.tecnica_text.delete('1.0', tk.END),
                                 '#444c56', hover_color='#5d6774',
                                 font_size=10, width=14, height=1)
        borrar_btn.grid(row=row, column=0, columnspan=COLS, pady=(10, 4), sticky='ew')
        
        # Imágenes de Batman aleatorias (bajo borrar técnica)
        row += 1
        self.batman_images = []
        self.batman_image_refs = []
        
        # Crear contenedor de 2 columnas para audio e imagen
        audio_container = tk.Frame(right_frame, bg=COLORS['bg_secondary'])
        audio_container.grid(row=row, column=0, columnspan=COLS, sticky='ew', pady=10)
        audio_container.columnconfigure(0, weight=1)  # Columna izquierda: audio
        audio_container.columnconfigure(1, weight=0)  # Columna derecha: imagen
        
        # --- COLUMNA IZQUIERDA: Info de audio ---
        audio_left = tk.Frame(audio_container, bg=COLORS['bg_secondary'])
        audio_left.grid(row=0, column=0, sticky='ew')
        audio_left.columnconfigure(0, weight=1)
        
        audio_label = tk.Label(audio_left, text="Audio Procesado:",
                             bg=COLORS['bg_secondary'],
                             fg=COLORS['text_primary'],
                             font=('Segoe UI', 12, 'bold'))
        audio_label.grid(row=0, column=0, sticky='w', pady=(0, 5))
        
        self.audio_info_label = tk.Label(audio_left, text="No hay audio",
                                       bg=COLORS['bg_secondary'],
                                       fg=COLORS['text_secondary'],
                                       font=('Segoe UI', 10))
        self.audio_info_label.grid(row=1, column=0, sticky='w', pady=(0, 5))
        
        self.download_audio_btn = StyledButton(audio_left, "Descargar Audio",
                                            self.download_audio,
                                            '#377ef0',
                                            fg_color='white',
                                            hover_color='#539bf5',
                                            font_size=11, width=22)
        # Forzar texto en blanco (también cuando está deshabilitado)
        self.download_audio_btn.config(fg='white', disabledforeground='white')
        self.download_audio_btn.grid(row=2, column=0, pady=5, sticky='w')
        self.download_audio_btn.config(state=tk.DISABLED)
        
        # --- COLUMNA DERECHA: Imagen de Batman ---
        # Cargar imagen aleatoria desde carpeta batman_images
        batman_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'batman_images')
        
        if not os.path.exists(batman_folder):
            batman_folder = os.path.join(os.getcwd(), 'batman_images')
        
        # Buscar todas las imágenes en la carpeta
        batman_paths = []
        if os.path.exists(batman_folder):
            import glob
            for ext in ['*.jpg', '*.jpeg', '*.png', '*.bmp']:
                batman_paths.extend(glob.glob(os.path.join(batman_folder, ext)))
        
        if not batman_paths:
            # Si no hay carpeta, usar imágenes por defecto
            batman_paths = [
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)), 'batman_images', 'joker.jpg')),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)), 'batman_images', 'batmanneal.jpg')),
            ]
        
        batman_paths = [p for p in batman_paths if os.path.exists(p)]
        
        # Cargar todas las imágenes disponibles para rotación
        if batman_paths:
            try:
                if PIL_AVAILABLE:
                    from PIL import Image as PILImage, ImageTk as PILImageTk
                    for img_path in batman_paths:
                        try:
                            img = PILImage.open(img_path)
                            # Altura fija de 300px
                            target_height = 300
                            aspect_ratio = img.width / img.height
                            target_width = int(target_height * aspect_ratio)
                            # Usar método de resize disponible
                            if hasattr(PILImage, 'LANCZOS'):
                                img = img.resize((target_width, target_height), PILImage.LANCZOS)
                            elif hasattr(PILImage, 'BICUBIC'):
                                img = img.resize((target_width, target_height), PILImage.BICUBIC)
                            else:
                                img = img.resize((target_width, target_height))
                            photo = PILImageTk.PhotoImage(img)
                            self.batman_images.append((photo, img_path))
                            self.image_refs.append(photo)
                        except Exception as e:
                            print(f"Error cargando imagen {img_path}: {e}")
                
                if self.batman_images:
                    # Crear frame con marco blanco
                    self.batman_frame = tk.Frame(audio_container, bg='white', highlightbackground='white', highlightthickness=2)
                    self.batman_frame.grid(row=0, column=1, padx=(20, 0))
                    
                    # Mostrar la primera imagen dentro del frame con marco
                    self.batman_label = tk.Label(self.batman_frame, image=self.batman_images[0][0], bg=COLORS['bg_secondary'])
                    self.batman_label.pack(padx=2, pady=2)  # Pequeño padding para el marco
                    print(f"Cargadas {len(self.batman_images)} imágenes de Batman para rotación")
                else:
                    print("No se pudieron cargar imágenes de Batman")
            except Exception as e:
                print(f"Error en carga de imágenes Batman: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("No se encontraron imágenes en la carpeta batman_images")
        
        # Separador
        row += 1
        separator = tk.Frame(right_frame, bg=COLORS['border'], height=2)
        separator.grid(row=row, column=0, columnspan=COLS, sticky='ew', pady=15)
    
    def check_services(self):
        """Verifica que los servicios estén disponibles"""
        if not self.recorder.is_available():
            self.set_status("⚠ PyAudio no disponible", COLORS['error'])
        elif not self.transcription.is_available():
            self.set_status("⚠ Configure GROQ_API_KEY o GEMINI_API_KEY en .env", COLORS['error'])
        else:
            # Mostrar qué servicio se usará
            services = []
            if self.transcription.is_groq_available():
                services.append("Groq")
            if self.transcription.is_gemini_available():
                services.append("Gemini")
            
            if services:
                self.set_status(f"✓ Listo (usará: {', '.join(services)})", COLORS['success'])
            else:
                self.set_status("⚠ Sin servicios de transcripción", COLORS['error'])
    
    def set_tecnica(self, texto):
        """Establece el texto de técnica"""
        self.tecnica_text.delete('1.0', tk.END)
        self.tecnica_text.insert('1.0', texto)
    
    # ==================== GRABACIÓN DE AUDIO ====================
    def toggle_recording(self):
        """Inicia o detiene la grabación"""
        if not self.recorder.is_available():
            messagebox.showerror("Error", "PyAudio no está disponible.")
            return
        
        if self.recorder.is_recording:
            self.stop_recording()
        else:
            self.start_recording()
    
    def start_recording(self):
        """Inicia la grabación"""
        success, msg = self.recorder.start_recording()
        if success:
            self.record_btn.config(text="⏹ Detener Dictado", bg=COLORS['btn_stop'])
            self.pause_btn.config(state=tk.NORMAL)
            self.retry_btn.config(state=tk.DISABLED)
            self.download_audio_btn.config(state=tk.DISABLED)
            self.set_status("Grabando...", COLORS['success'])
            # LED amarillo indicando que está activo pero sin audio aún
            if hasattr(self, 'mic_led'):
                self._draw_led('#ffff00')
        else:
            messagebox.showerror("Error", msg)
    
    def stop_recording(self):
        """Detiene la grabación"""
        self.record_btn.config(text="▶ Empezar Dictado", state=tk.DISABLED)
        self.pause_btn.config(state=tk.DISABLED)
        self.set_status("Procesando audio...", COLORS['processing'])
        # LED gris indicando inactivo
        if hasattr(self, 'mic_led'):
            self._draw_led('gray')
        
        thread = threading.Thread(target=self._stop_recording_thread)
        thread.start()
    
    def _stop_recording_thread(self):
        """Thread para detener grabación y procesar"""
        audio_file, msg = self.recorder.stop_recording()
        
        if audio_file:
            self.current_audio_file = audio_file
            self.root.after(0, self._on_recording_stopped, audio_file)
        else:
            self.root.after(0, self._on_recording_error, msg)
    
    def _on_recording_stopped(self, audio_file):
        """Callback cuando la grabación se detuvo correctamente"""
        self.audio_info_label.config(text=f"Audio: {os.path.basename(audio_file)}",
                                    fg=COLORS['text_primary'])
        self.download_audio_btn.config(state=tk.NORMAL)
        self.retry_btn.config(state=tk.NORMAL)
        self.record_btn.config(state=tk.NORMAL, bg=COLORS['btn_record'])
        self.process_audio(audio_file)
    
    def _on_recording_error(self, msg):
        """Callback cuando hay error en grabación"""
        self.set_status(f"Error: {msg}", COLORS['error'])
        self.record_btn.config(state=tk.NORMAL, bg=COLORS['btn_record'])
    
    def toggle_pause(self):
        """Pausa o reanuda la grabación"""
        if self.recorder.is_paused:
            self.recorder.resume_recording()
            self.pause_btn.config(text="⏸ Pausar", bg=COLORS['btn_pause'])
            self.set_status("Grabando...", COLORS['success'])
        else:
            self.recorder.pause_recording()
            self.pause_btn.config(text="▶ Reanudar", bg=COLORS['btn_success'])
            self.set_status("Pausado", COLORS['idle'])
    
    def on_recording_status_change(self, status):
        """Callback de cambio de estado de grabación"""
        if status == "recording":
            self.root.after(0, lambda: self.set_status("Grabando...", COLORS['success']))
        elif status == "paused":
            self.root.after(0, lambda: self.set_status("Pausado", COLORS['idle']))
    
    def on_recording_time_update(self, seconds):
        """Callback de actualización de tiempo"""
        formatted = self.text_processor.format_time(seconds)
        self.root.after(0, lambda: self.time_label.config(text=f"Tiempo: {formatted}"))
        
        if seconds >= RECORDING_WARNING_TIME and seconds < RECORDING_WARNING_TIME + 2:
            self.root.after(0, lambda: self.set_status("⚠ Cerca del límite de tiempo", COLORS['error']))

    def _update_volume(self, value):
        if value is None:
            return
        if hasattr(self, 'volume_bar') and self.volume_bar:
            self.volume_bar['value'] = int(value)
        # Actualizar LED según volumen
        if hasattr(self, 'mic_led'):
            if int(value) > 5:
                self._draw_led('#00ff00')  # Verde cuando hay audio
            elif int(value) > 0:
                self._draw_led('#ffff00')  # Amarillo cuando hay poco audio
            else:
                self._draw_led('#ff0000')  # Rojo cuando no hay audio pero grabando
    
    def _on_audio_level(self, value):
        """Callback directo del AudioRecorder para actualizar volumen"""
        self.root.after(0, self._update_volume, value)
    
    def _draw_led(self, color):
        """Dibuja un indicador LED circular"""
        if hasattr(self, 'mic_led'):
            self.mic_led.delete('all')
            self.mic_led.create_oval(2, 2, 18, 18, fill=color, outline='white', width=2)

    def _setup_comic_section(self):
        # Create a decorative comic/story panel with Batman images if available
        try:
            base_container = self.main_frame
            self.comic_frame = tk.LabelFrame(base_container, text="Estética Comics",
                                            bg=COLORS['bg_secondary'],
                                            fg=COLORS['text_primary'],
                                            font=('Segoe UI', 12, 'bold'),
                                            padx=10, pady=10)
            self.comic_frame.grid(row=4, column=0, columnspan=2, sticky='ew', pady=(0,10))
            self.comic_frame.columnconfigure(0, weight=1)
            # Cargar imágenes si PIL disponible
            if PIL_AVAILABLE:
                images = []
                img_paths = [
                    r"C:\Users\batju\Desktop\dictado-radiologico-main\joker.jpg",
                    r"C:\Users\batju\Desktop\dictado-radiologico-main\batmanneal.jpg",
                ]
                for p in img_paths:
                    if os.path.exists(p):
                        from PIL import Image as PILImage, ImageTk as PILImageTk
                        try:
                            img = PILImage.open(p)
                            # Uso de método de resize robusto
                            if hasattr(PILImage, 'BICUBIC'):
                                img = img.resize((180, 240), PILImage.BICUBIC)
                            elif hasattr(PILImage, 'ANTIALIAS'):
                                img = img.resize((180, 240), PILImage.ANTIALIAS)
                            elif hasattr(PILImage, 'LANCZOS'):
                                img = img.resize((180, 240), PILImage.LANCZOS)
                            photo = PILImageTk.PhotoImage(img)
                            lbl = tk.Label(self.comic_frame, image=photo, bg=COLORS['bg_secondary'])
                            lbl.pack(side=tk.LEFT, padx=6)
                            self.image_refs.append(photo)
                            images.append(photo)
                        except Exception:
                            pass
                if not images:
                    tk.Label(self.comic_frame, text="Batman/Joker decorativo", bg=COLORS['bg_secondary'],
                             fg=COLORS['text_primary']).pack()
            else:
                tk.Label(self.comic_frame, text="Pillow no instalado para imágenes", bg=COLORS['bg_secondary'],
                         fg=COLORS['text_primary']).pack()
        except Exception as e:
            # Si falla, no romper la app
            print("Aviso: no se pudo cargar la estética Batman.", e)

    def _test_microphone(self):
        """Prueba el micrófono mostrando nivel en tiempo real"""
        if not self.recorder.is_available():
            messagebox.showwarning("Micrófono", "PyAudio no está disponible.\nInstálalo con: pip install pyaudio")
            return
        
        self.set_status("Probando micrófono... habla ahora", COLORS['processing'])
        
        try:
            import pyaudio
            import struct
            
            p = self.recorder.audio
            if p is None:
                raise Exception("PyAudio no inicializado correctamente")
            
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=1024)
            
            self._draw_led('#ffff00')  # Amarillo durante prueba
            
            for i in range(50):  # 5 segundos de prueba
                data = stream.read(1024, exception_on_overflow=False)
                count = len(data) // 2
                if count > 0:
                    fmt = "<" + str(count) + "h"
                    samples = struct.unpack(fmt, data)
                    mean_square = sum((s*s) for s in samples) / count
                    rms = mean_square ** 0.5
                    vol = int(min(100, max(0, (rms / 32768) * 100)))
                    self.volume_bar['value'] = vol
                    if vol > 10:
                        self._draw_led('#00ff00')  # Verde si hay audio
                    else:
                        self._draw_led('#ff0000')  # Rojo si no hay audio
                self.root.update()
                time.sleep(0.1)
            
            stream.stop_stream()
            stream.close()
            self.set_status("Prueba completada", COLORS['success'])
            self._draw_led('gray')
            
        except Exception as e:
            self.set_status(f"Error: {str(e)}", COLORS['error'])
            self._draw_led('gray')
            messagebox.showerror("Error de micrófono", str(e))
    
    def _toggle_sim_volume(self):
        # Start/stop simulated volume updates for testing without mic input
        if getattr(self, 'sim_vol_var', None) and self.sim_vol_var.get():
            self.sim_vol_running = True
            import threading
            self.sim_vol_thread = threading.Thread(target=self._simulate_volume_loop, daemon=True)
            self.sim_vol_thread.start()
        else:
            self.sim_vol_running = False

    def _simulate_volume_loop(self):
        t = 0.0
        while getattr(self, 'sim_vol_running', False):
            vol = int((time.time() * 2) % 100)  # simple placeholder pattern
            self.root.after(0, self._update_volume, vol)
            time.sleep(0.15)

    def open_batman_viewer(self):
        # Ventana modal con imágenes estilo Batman/Joker
        if not PIL_AVAILABLE:
            try:
                from tkinter import messagebox
                messagebox.showinfo("Batman Visuals", "Pillow no está instalado; imágenes no disponibles.")
            except Exception:
                pass
            return
        viewer = tk.Toplevel(self.root)
        viewer.title("Batman Visuals")
        viewer.geometry("720x420")
        viewer.configure(bg=COLORS['bg_primary'])
        container = tk.Frame(viewer, bg=COLORS['bg_primary'])
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        self.viewer_image_refs = []

        image_paths = [
            r"C:\Users\batju\Desktop\dictado-radiologico-main\joker.jpg",
            r"C:\Users\batju\Desktop\dictado-radiologico-main\batmanneal.jpg",
        ]
        col = 0
        for p in image_paths:
            if os.path.exists(p):
                try:
                    from PIL import Image as PILImage, ImageTk as PILImageTk
                    img = PILImage.open(p)
                    img = img.resize((320, 360), PILImage.BICUBIC) if hasattr(PILImage, 'BICUBIC') else img
                    photo = PILImageTk.PhotoImage(img)
                    lbl = tk.Label(container, image=photo, bg=COLORS['bg_primary'])
                    lbl.grid(row=0, column=col, padx=10, pady=5)
                    self.viewer_image_refs.append(photo)
                    col += 1
                except Exception:
                    pass

    
    # ==================== PROCESAMIENTO DE AUDIO ====================
    def process_audio(self, audio_file):
        """Procesa el archivo de audio"""
        if not self.transcription.is_available():
            messagebox.showerror("Error", "Servicio de transcripción no disponible.")
            self.set_status("Error: API no configurada", COLORS['error'])
            self.record_btn.config(state=tk.NORMAL)
            return
        
        self.is_processing = True
        self.set_status("Transcribiendo audio...", COLORS['processing'])
        
        thread = threading.Thread(target=self._process_audio_thread, args=(audio_file,))
        thread.start()
    
    def _process_audio_thread(self, audio_file):
        """Thread de procesamiento"""
        try:
            print(f"Procesando archivo: {audio_file}")
            
            text, compressed_file, error = self.transcription.transcribe_audio(
                audio_file,
                on_status=lambda s: self.root.after(0, lambda: self.set_status(s, COLORS['processing']))
            )
            
            print(f"Transcripción completada. Error: {error}")
            print(f"Archivo comprimido: {compressed_file}")
            
            if error:
                self.root.after(0, self._on_processing_error, error)
                return
            
            # Guardar referencia del archivo comprimido
            self.compressed_audio_file = compressed_file
            
            # Actualizar label con el archivo comprimido
            filename = os.path.basename(compressed_file) if compressed_file else "desconocido"
            ext = "OGG" if compressed_file and compressed_file.endswith('.ogg') else "WAV"
            
            print(f"Mostrando en interfaz: {filename} ({ext})")
            
            if compressed_file:
                self.root.after(0, lambda: self.audio_info_label.config(
                    text=f"📁 {filename} ({ext})",
                    fg=COLORS['text_primary']
                ))
            
            self.root.after(0, lambda: self.set_status("Puliendo texto...", COLORS['processing']))
            processed_text = self.text_processor.process_text(text, self.vocabulary.get_vocabulary())
            
            self.root.after(0, self._on_processing_complete, processed_text)
            
        except Exception as e:
            self.root.after(0, self._on_processing_error, str(e))
    
    def _on_processing_complete(self, text):
        """Callback cuando el procesamiento completa"""
        self.insert_text_at_cursor(text)
        self.set_status("✓ Texto insertado con éxito", COLORS['success'])
        self.record_btn.config(state=tk.NORMAL)
        self.retry_btn.config(state=tk.NORMAL)
        self.is_processing = False
    
    def _on_processing_error(self, error):
        """Callback cuando hay error en procesamiento"""
        self.set_status(f"✗ Error: {error}", COLORS['error'])
        self.record_btn.config(state=tk.NORMAL)
        self.retry_btn.config(state=tk.NORMAL)
        self.is_processing = False
        messagebox.showerror("Error de procesamiento", str(error))
    
    def retry_processing(self):
        """Reenvía el último audio para procesamiento"""
        if self.current_audio_file and os.path.exists(self.current_audio_file):
            self.process_audio(self.current_audio_file)
        else:
            messagebox.showwarning("Advertencia", "No hay audio previo para reenviar")
    
    def insert_text_at_cursor(self, text):
        """Inserta texto en la posición del cursor"""
        if text:
            try:
                sel_start = self.informe_text.index(tk.SEL_FIRST)
                sel_end = self.informe_text.index(tk.SEL_LAST)
                self.informe_text.delete(sel_start, sel_end)
                self.informe_text.insert(sel_start, text)
            except tk.TclError:
                cursor_pos = self.informe_text.index(tk.INSERT)
                current_text = self.informe_text.get('1.0', tk.END)
                
                if current_text.strip() and cursor_pos != '1.0':
                    prev_char_idx = self.informe_text.index(f"{cursor_pos} - 1 chars")
                    prev_char = self.informe_text.get(prev_char_idx, cursor_pos)
                    if prev_char and not prev_char.isspace():
                        text = ' ' + text
                
                self.informe_text.insert(cursor_pos, text)
    
    # ==================== FRASES CÉLEBRES ====================
    def _start_quotes_rotation(self):
        """Inicia la rotación de frases célebres con efecto fade"""
        self._fade_out_quote()
    
    def _fade_out_quote(self):
        """Efecto fade out de la frase actual"""
        if not self.quote_label or not self.quote_author_label:
            return
        
        # Colores de inicio (visibles) a fin (transparente/bg)
        steps = 20  # Número de pasos para el fade
        duration = 1000  # ms total para fade out
        step_duration = duration // steps
        
        def fade_step(step):
            if step > steps:
                # Cambiar a una frase aleatoria (evitando repetir la misma)
                available_indices = [i for i in range(len(self.quotes)) if i != self.current_quote_index]
                self.current_quote_index = random.choice(available_indices) if available_indices else 0
                quote, author = self.quotes[self.current_quote_index]
                self.quote_label.config(text=quote)
                self.quote_author_label.config(text=f"— {author}")
                self._fade_in_quote()
                return
            
            # Calcular color interpolado (de text_primary a bg_secondary)
            ratio = step / steps
            r1, g1, b1 = self._hex_to_rgb(COLORS['text_primary'])
            r2, g2, b2 = self._hex_to_rgb(COLORS['bg_secondary'])
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            self.quote_label.config(fg=color)
            self.quote_author_label.config(fg=color)
            
            self.root.after(step_duration, lambda: fade_step(step + 1))
        
        fade_step(0)
    
    def _fade_in_quote(self):
        """Efecto fade in de la nueva frase"""
        if not self.quote_label or not self.quote_author_label:
            return
        
        steps = 20
        duration = 1000  # ms total para fade in
        step_duration = duration // steps
        
        def fade_step(step):
            if step > steps:
                # Esperar 30 segundos antes de cambiar
                self.root.after(28000, self._fade_out_quote)  # 30s total - 2s de fade
                return
            
            # Calcular color interpolado (de bg_secondary a text_primary)
            ratio = step / steps
            r1, g1, b1 = self._hex_to_rgb(COLORS['bg_secondary'])
            r2, g2, b2 = self._hex_to_rgb(COLORS['text_primary'])
            r = int(r1 + (r2 - r1) * ratio)
            g = int(g1 + (g2 - g1) * ratio)
            b = int(b1 + (b2 - b1) * ratio)
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            self.quote_label.config(fg=color)
            self.quote_author_label.config(fg=color)
            
            self.root.after(step_duration, lambda: fade_step(step + 1))
        
        fade_step(0)
    
    # ==================== ROTACIÓN DE IMÁGENES BATMAN ====================
    def _start_batman_rotation(self):
        """Inicia la rotación de imágenes de Batman cada minuto"""
        if len(self.batman_images) < 2:
            return  # No hay suficientes imágenes para rotar
        
        # Esperar 1 minuto antes del primer cambio
        self.root.after(60000, self._rotate_batman_image)
    
    def _rotate_batman_image(self):
        """Cambia a la siguiente imagen de Batman con efecto fade"""
        if not self.batman_label or len(self.batman_images) < 2:
            return
        
        # Cambiar a imagen aleatoria (evitando repetir)
        available_indices = [i for i in range(len(self.batman_images)) if i != self.current_batman_index]
        new_index = random.choice(available_indices) if available_indices else 0
        
        self.current_batman_index = new_index
        new_photo = self.batman_images[new_index][0]
        
        # Actualizar la imagen con efecto fade (cambio gradual de opacidad simulado con retraso)
        self._fade_batman_image(new_photo)
        
        # Programar siguiente rotación en 1 minuto
        self.root.after(60000, self._rotate_batman_image)
    
    def _fade_batman_image(self, new_photo):
        """Aplica efecto de transición a la nueva imagen"""
        if not self.batman_label:
            return
        
        # Simular fade con pequeños pasos
        steps = 10
        duration = 500  # 500ms para la transición
        step_duration = duration // steps
        
        def fade_step(step):
            if step == 0:
                # Inicio: mostrar imagen con baja opacidad (simulado)
                self.batman_label.config(image=new_photo)
                self.batman_label.image = new_photo  # Mantener referencia
                self.root.after(step_duration, lambda: fade_step(step + 1))
            elif step < steps:
                # Pasos intermedios
                self.root.after(step_duration, lambda: fade_step(step + 1))
            else:
                # Final: imagen completamente visible
                pass
        
        fade_step(0)
    
    def _hex_to_rgb(self, hex_color):
        """Convierte color hex a RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    # ==================== BOTONES DE ACCIÓN ====================
    def copy_full_report(self):
        """Copia el informe completo al portapapeles"""
        tecnica = self.tecnica_text.get('1.0', tk.END).strip()
        informe = self.informe_text.get('1.0', tk.END).strip()
        
        full_report = ""
        if tecnica:
            full_report += tecnica + "\n\n"
        if informe:
            full_report += informe
        
        if full_report:
            self.root.clipboard_clear()
            self.root.clipboard_append(full_report)
            self.set_status("✓ Texto copiado al portapapeles", COLORS['success'])
        else:
            messagebox.showinfo("Información", "No hay texto para copiar")
    
    def reset_report(self):
        """Limpia el informe"""
        if messagebox.askyesno("Confirmar", "¿Seguro que quieres borrar TODO el informe y la técnica?"):
            self.tecnica_text.delete('1.0', tk.END)
            self.informe_text.delete('1.0', tk.END)
            self.set_status("Informe reseteado", COLORS['idle'])
    
    def upload_audio(self):
        """Permite subir un archivo de audio"""
        filename = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[('Archivos de audio', '*.wav *.mp3 *.ogg *.m4a *.webm'), ('Todos', '*.*')]
        )
        
        if filename:
            self.current_audio_file = filename
            self.audio_info_label.config(text=f"Audio: {os.path.basename(filename)}",
                                        fg=COLORS['text_primary'])
            self.download_audio_btn.config(state=tk.NORMAL)
            self.retry_btn.config(state=tk.NORMAL)
            self.process_audio(filename)
    
    def download_audio(self):
        """Descarga el audio comprimido (OGG)"""
        # Usar archivo comprimido si existe, sino el original
        file_to_download = self.compressed_audio_file or self.current_audio_file
        
        if file_to_download and os.path.exists(file_to_download):
            # Determinar extensión
            ext = '.ogg' if file_to_download.endswith('.ogg') else '.wav'
            
            dest = filedialog.asksaveasfilename(
                defaultextension=ext,
                filetypes=[('Audio comprimido OGG', '*.ogg'), ('Audio WAV', '*.wav')],
                initialfile=f"dictado-radiologico-{self.get_timestamp()}{ext}"
            )
            if dest:
                import shutil
                shutil.copy(file_to_download, dest)
                self.set_status(f"✓ Audio guardado ({ext})", COLORS['success'])
    
    def get_timestamp(self):
        """Devuelve timestamp actual"""
        from datetime import datetime
        return datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def set_status(self, text, color):
        """Actualiza el texto de estado"""
        self.status_label.config(text=text, fg=color)
    
    # ==================== JUANIZADOR ====================
    def open_juanizador(self):
        """Abre la ventana del Juanizador"""
        informe = self.informe_text.get('1.0', tk.END).strip()
        if not informe:
            messagebox.showinfo("Información", "No hay texto en el informe para analizar")
            return
        
        JuanizadorWindow(self.root, informe, self.juanizador, self)
    
    # ==================== VOCABULARIO ====================
    def open_vocabulary_manager(self):
        """Abre el gestor de vocabulario"""
        VocabularyWindow(self.root, self.vocabulary, self.text_processor)


class JuanizadorWindow:
    """Ventana del Asistente Juanizador estilizada"""
    def __init__(self, parent, text_to_analyze, juanizador_service, main_app):
        self.window = tk.Toplevel(parent)
        self.window.title("Asistente de Informes Radiológicos - Juanizador")
        self.window.state('zoomed')  # Pantalla completa
        self.window.configure(bg=COLORS['bg_primary'])
        
        self.juanizador = juanizador_service
        self.main_app = main_app
        self.categorized_findings = {}
        
        self.setup_ui(text_to_analyze)
    
    def setup_ui(self, initial_text):
        """Configura la UI estilizada del Juanizador"""
        main_frame = tk.Frame(self.window, bg=COLORS['bg_primary'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = tk.Label(main_frame, text="Asistente de Informes Radiológicos",
                              bg=COLORS['bg_primary'],
                              fg=COLORS['text_primary'],
                              font=('Segoe UI', 24, 'bold'))
        title_label.pack(anchor='w', pady=(0, 20))
        
        # Panel de selección de técnica
        tech_frame = tk.LabelFrame(main_frame, text=" Configuración del Estudio ",
                                  bg=COLORS['bg_secondary'],
                                  fg=COLORS['text_primary'],
                                  font=('Segoe UI', 14, 'bold'),
                                  padx=15, pady=15)
        tech_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Controles de técnica
        tech_controls = tk.Frame(tech_frame, bg=COLORS['bg_secondary'])
        tech_controls.pack(fill=tk.X)
        
        # Técnica
        tk.Label(tech_controls, text="Técnica:",
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_primary'],
                font=('Segoe UI', 12)).pack(side=tk.LEFT, padx=(0, 5))
        
        self.tech_combo = ttk.Combobox(tech_controls, values=['TAC', 'RM', 'Ecografía'],
                                      state='readonly', width=12, font=('Segoe UI', 11))
        self.tech_combo.set('TAC')
        self.tech_combo.pack(side=tk.LEFT, padx=5)
        self.tech_combo.bind('<<ComboboxSelected>>', self.on_tech_change)
        
        # Alcance TAC
        self.tac_scope_label = tk.Label(tech_controls, text="Alcance:",
                                       bg=COLORS['bg_secondary'],
                                       fg=COLORS['text_primary'],
                                       font=('Segoe UI', 12))
        self.tac_scope_label.pack(side=tk.LEFT, padx=(20, 5))
        
        self.tac_scope_combo = ttk.Combobox(tech_controls,
                                           values=['Toracoabdominal', 'Torácico', 'Abdominal'],
                                           state='readonly', width=15, font=('Segoe UI', 11))
        self.tac_scope_combo.set('Toracoabdominal')
        self.tac_scope_combo.pack(side=tk.LEFT, padx=5)
        
        # Tipo RM (oculto inicialmente)
        self.rm_type_label = tk.Label(tech_controls, text="Tipo RM:",
                                     bg=COLORS['bg_secondary'],
                                     fg=COLORS['text_primary'],
                                     font=('Segoe UI', 12))
        self.rm_type_combo = ttk.Combobox(tech_controls,
                                          values=['RM Hepática', 'ColangioRM', 'EnteroRM',
                                                 'RM Pelvis NEO', 'RM Pelvis FIST'],
                                          state='readonly', width=18, font=('Segoe UI', 11))
        self.rm_type_combo.set('RM Hepática')
        
        # Contraste
        tk.Label(tech_controls, text="Contraste:",
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_primary'],
                font=('Segoe UI', 12)).pack(side=tk.LEFT, padx=(20, 5))
        
        self.contrast_combo = ttk.Combobox(tech_controls, values=['Sin contraste', 'Con contraste'],
                                          state='readonly', width=14, font=('Segoe UI', 11))
        self.contrast_combo.set('Con contraste')
        self.contrast_combo.pack(side=tk.LEFT, padx=5)
        self.contrast_combo.bind('<<ComboboxSelected>>', self.on_contrast_change)
        
        # Fases (oculto inicialmente)
        self.phase_frame = tk.Frame(tech_frame, bg=COLORS['bg_secondary'])
        tk.Label(self.phase_frame, text="Fases:",
                bg=COLORS['bg_secondary'],
                fg=COLORS['text_primary'],
                font=('Segoe UI', 12)).pack(side=tk.LEFT)
        
        self.var_arterial = tk.BooleanVar()
        self.var_portal = tk.BooleanVar()
        self.var_tardia = tk.BooleanVar()
        
        tk.Checkbutton(self.phase_frame, text="Arterial", variable=self.var_arterial,
                      bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                      selectcolor=COLORS['bg_primary'],
                      font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(self.phase_frame, text="Portal", variable=self.var_portal,
                      bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                      selectcolor=COLORS['bg_primary'],
                      font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=5)
        tk.Checkbutton(self.phase_frame, text="Tardía", variable=self.var_tardia,
                      bg=COLORS['bg_secondary'], fg=COLORS['text_primary'],
                      selectcolor=COLORS['bg_primary'],
                      font=('Segoe UI', 11)).pack(side=tk.LEFT, padx=5)
        
        # Panel de entrada
        input_frame = tk.LabelFrame(main_frame, text=" Hallazgos ",
                                   bg=COLORS['bg_secondary'],
                                   fg=COLORS['text_primary'],
                                   font=('Segoe UI', 14, 'bold'),
                                   padx=15, pady=15)
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.hallazgos_text = tk.Text(input_frame, height=6, wrap=tk.WORD,
                                     font=self.main_app.text_font,
                                     bg=COLORS['bg_secondary'],
                                     fg=COLORS['text_primary'],
                                     insertbackground=COLORS['text_primary'],
                                     relief=tk.FLAT,
                                     highlightbackground=COLORS['border'],
                                     highlightthickness=1,
                                     padx=12, pady=12)
        self.hallazgos_text.pack(fill=tk.BOTH, expand=True)
        self.hallazgos_text.insert('1.0', initial_text)
        
        # Botones de acción
        btn_frame = tk.Frame(input_frame, bg=COLORS['bg_secondary'])
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        StyledButton(btn_frame, "Categorizar Hallazgos",
                    self.categorize, COLORS['btn_record'],
                    font_size=12, width=20).pack(side=tk.LEFT, padx=5)
        
        StyledButton(btn_frame, "Limpiar",
                    self.clear_all, '#444c56',
                    hover_color='#5d6774',
                    font_size=12, width=12).pack(side=tk.LEFT, padx=5)
        
        StyledButton(btn_frame, "Volver a Dictado",
                    self.close, COLORS['btn_stop'],
                    hover_color=COLORS['btn_stop_hover'],
                    font_size=12, width=16).pack(side=tk.RIGHT, padx=5)
        
        # Panel dividido para categorías e informe
        bottom_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.columnconfigure(1, weight=1)
        
        # Panel de categorías
        cat_frame = tk.LabelFrame(bottom_frame, text=" Hallazgos Categorizados ",
                                 bg=COLORS['bg_secondary'],
                                 fg=COLORS['text_primary'],
                                 font=('Segoe UI', 14, 'bold'),
                                 padx=15, pady=15)
        cat_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        
        self.cat_text = tk.Text(cat_frame, wrap=tk.WORD,
                               font=self.main_app.text_font,
                               bg=COLORS['bg_secondary'],
                               fg=COLORS['text_primary'],
                               relief=tk.FLAT,
                               highlightbackground=COLORS['border'],
                               highlightthickness=1,
                               padx=12, pady=12,
                               state=tk.DISABLED)
        self.cat_text.pack(fill=tk.BOTH, expand=True)
        
        # Panel de informe final
        report_frame = tk.LabelFrame(bottom_frame, text=" Informe Final ",
                                    bg=COLORS['bg_secondary'],
                                    fg=COLORS['text_primary'],
                                    font=('Segoe UI', 14, 'bold'),
                                    padx=15, pady=15)
        report_frame.grid(row=0, column=1, sticky='nsew')
        
        # Botones del informe
        report_btn_frame = tk.Frame(report_frame, bg=COLORS['bg_secondary'])
        report_btn_frame.pack(fill=tk.X, pady=(0, 10))
        
        StyledButton(report_btn_frame, "Generar Informe",
                    self.generate_report, COLORS['btn_success'],
                    hover_color='#218838',
                    font_size=12, width=16).pack(side=tk.LEFT, padx=5)
        
        StyledButton(report_btn_frame, "Copiar Informe",
                    self.copy_report, COLORS['btn_copy'],
                    fg_color=COLORS['btn_pause_text'],
                    hover_color='#f0b72f',
                    font_size=12, width=14).pack(side=tk.LEFT, padx=5)
        
        StyledButton(report_btn_frame, "Transferir a Dictado",
                    self.transfer_to_main, COLORS['btn_juanizar'],
                    hover_color='#28a9c2',
                    font_size=12, width=18).pack(side=tk.LEFT, padx=5)
        
        self.report_text = tk.Text(report_frame, wrap=tk.WORD,
                                  font=self.main_app.text_font,
                                  bg=COLORS['bg_secondary'],
                                  fg=COLORS['text_primary'],
                                  insertbackground=COLORS['text_primary'],
                                  relief=tk.FLAT,
                                  highlightbackground=COLORS['border'],
                                  highlightthickness=1,
                                  padx=12, pady=12)
        self.report_text.pack(fill=tk.BOTH, expand=True)
        
        self.on_tech_change()
    
    def on_tech_change(self, event=None):
        """Maneja cambio de técnica"""
        tech = self.tech_combo.get()
        
        if tech == 'TAC':
            self.tac_scope_label.pack(side=tk.LEFT, padx=(20, 5))
            self.tac_scope_combo.pack(side=tk.LEFT, padx=5)
            self.rm_type_label.pack_forget()
            self.rm_type_combo.pack_forget()
        elif tech == 'RM':
            self.tac_scope_label.pack_forget()
            self.tac_scope_combo.pack_forget()
            self.rm_type_label.pack(side=tk.LEFT, padx=(20, 5))
            self.rm_type_combo.pack(side=tk.LEFT, padx=5)
        else:  # Eco
            self.tac_scope_label.pack_forget()
            self.tac_scope_combo.pack_forget()
            self.rm_type_label.pack_forget()
            self.rm_type_combo.pack_forget()
        
        self.on_contrast_change()
    
    def on_contrast_change(self, event=None):
        """Maneja cambio de contraste"""
        tech = self.tech_combo.get()
        contrast = self.contrast_combo.get() == 'Con contraste'
        
        if tech == 'TAC' and contrast:
            self.phase_frame.pack(fill=tk.X, pady=(10, 0))
        else:
            self.phase_frame.pack_forget()
    
    def categorize(self):
        """Categoriza los hallazgos"""
        transcript = self.hallazgos_text.get('1.0', tk.END).strip()
        if not transcript:
            messagebox.showwarning("Advertencia", "No hay hallazgos para categorizar")
            return
        
        available_cats = self.juanizador.get_available_categories(
            self.tech_combo.get().lower(),
            self.tac_scope_combo.get().lower().replace(' ', '') if self.tech_combo.get() == 'TAC' else None,
            self.rm_type_combo.get().lower().replace(' ', '-') if self.tech_combo.get() == 'RM' else None
        )
        
        def do_categorize():
            result, error = self.juanizador.categorize_findings(
                transcript, available_cats
            )
            
            if error:
                self.window.after(0, lambda: messagebox.showerror("Error", error))
            else:
                self.categorized_findings = result
                self.window.after(0, self.display_categories)
        
        thread = threading.Thread(target=do_categorize)
        thread.start()
    
    def display_categories(self):
        """Muestra las categorías"""
        self.cat_text.config(state=tk.NORMAL)
        self.cat_text.delete('1.0', tk.END)
        
        for cat_id, findings in self.categorized_findings.items():
            if findings:
                cat_name = next((c['name'] for c in self.juanizador.categories if str(c['id']) == cat_id), cat_id)
                self.cat_text.insert(tk.END, f"\n{cat_name}:\n")
                for finding in findings:
                    self.cat_text.insert(tk.END, f"  • {finding}\n")
        
        self.cat_text.config(state=tk.DISABLED)
    
    def generate_report(self):
        """Genera el informe completo"""
        if not self.categorized_findings:
            messagebox.showwarning("Advertencia", "Primero debe categorizar los hallazgos")
            return
        
        phases = []
        if self.var_arterial.get():
            phases.append('arterial')
        if self.var_portal.get():
            phases.append('portal')
        if self.var_tardia.get():
            phases.append('tardia')
        
        def do_generate():
            result, error = self.juanizador.generate_report(
                self.tech_combo.get().lower(),
                self.tac_scope_combo.get().lower().replace(' ', '') if self.tech_combo.get() == 'TAC' else None,
                self.rm_type_combo.get().lower().replace(' ', '-') if self.tech_combo.get() == 'RM' else None,
                self.contrast_combo.get() == 'Con contraste',
                phases,
                self.juanizador.get_available_categories(
                    self.tech_combo.get().lower(),
                    self.tac_scope_combo.get().lower().replace(' ', '') if self.tech_combo.get() == 'TAC' else None,
                    self.rm_type_combo.get().lower().replace(' ', '-') if self.tech_combo.get() == 'RM' else None
                )
            )
            
            if error:
                self.window.after(0, lambda: messagebox.showerror("Error", error))
            else:
                self.window.after(0, lambda: self.display_report(result))
        
        thread = threading.Thread(target=do_generate)
        thread.start()
    
    def display_report(self, report):
        """Muestra el informe generado"""
        self.report_text.delete('1.0', tk.END)
        self.report_text.insert('1.0', report['full_report'])
    
    def copy_report(self):
        """Copia el informe al portapapeles"""
        report = self.report_text.get('1.0', tk.END).strip()
        if report:
            self.window.clipboard_clear()
            self.window.clipboard_append(report)
            messagebox.showinfo("Éxito", "Informe copiado al portapapeles")
    
    def transfer_to_main(self):
        """Transfiere el informe a la ventana principal"""
        report = self.report_text.get('1.0', tk.END).strip()
        if report:
            lines = report.split('\n')
            if lines:
                self.main_app.tecnica_text.delete('1.0', tk.END)
                self.main_app.tecnica_text.insert('1.0', lines[0])
                
                if len(lines) > 1:
                    self.main_app.informe_text.delete('1.0', tk.END)
                    self.main_app.informe_text.insert('1.0', '\n'.join(lines[1:]).strip())
            
            self.close()
    
    def clear_all(self):
        """Limpia todo"""
        self.hallazgos_text.delete('1.0', tk.END)
        self.cat_text.config(state=tk.NORMAL)
        self.cat_text.delete('1.0', tk.END)
        self.cat_text.config(state=tk.DISABLED)
        self.report_text.delete('1.0', tk.END)
        self.categorized_findings = {}
    
    def close(self):
        """Cierra la ventana"""
        self.window.destroy()


class VocabularyWindow:
    """Ventana de gestión de vocabulario estilizada"""
    def __init__(self, parent, vocabulary_manager, text_processor):
        self.window = tk.Toplevel(parent)
        self.window.title("Gestionar Vocabulario Personalizado")
        self.window.geometry("800x600")
        self.window.configure(bg=COLORS['bg_primary'])
        
        self.vocab = vocabulary_manager
        self.processor = text_processor
        
        self.setup_ui()
        self.load_vocabulary()
    
    def setup_ui(self):
        """Configura la UI estilizada"""
        main_frame = tk.Frame(self.window, bg=COLORS['bg_primary'], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = tk.Label(main_frame, text="Gestionar Vocabulario Personalizado",
                              bg=COLORS['bg_primary'],
                              fg=COLORS['text_primary'],
                              font=('Segoe UI', 20, 'bold'))
        title_label.pack(anchor='w', pady=(0, 10))
        
        # Instrucciones
        instr_label = tk.Label(main_frame, 
                              text="Las claves (texto incorrecto) se guardan en minúsculas.",
                              bg=COLORS['bg_primary'],
                              fg=COLORS['text_secondary'],
                              font=('Segoe UI', 10, 'italic'))
        instr_label.pack(anchor='w', pady=(0, 15))
        
        # Frame para la lista
        list_frame = tk.Frame(main_frame, bg=COLORS['bg_secondary'],
                             highlightbackground=COLORS['border'],
                             highlightthickness=1)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        # Treeview estilizado
        style = ttk.Style()
        style.configure("Custom.Treeview",
                       background=COLORS['bg_secondary'],
                       foreground=COLORS['text_primary'],
                       fieldbackground=COLORS['bg_secondary'],
                       font=('Segoe UI', 11))
        style.configure("Custom.Treeview.Heading",
                       background=COLORS['bg_secondary'],
                       foreground=COLORS['text_primary'],
                       font=('Segoe UI', 11, 'bold'))
        
        columns = ('incorrecto', 'correcto')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings',
                                style="Custom.Treeview")
        self.tree.heading('incorrecto', text='Texto Incorrecto')
        self.tree.heading('correcto', text='Texto Correcto')
        self.tree.column('incorrecto', width=350)
        self.tree.column('correcto', width=350)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=5)
        
        # Botones
        btn_frame = tk.Frame(main_frame, bg=COLORS['bg_primary'])
        btn_frame.pack(fill=tk.X)
        
        StyledButton(btn_frame, "Añadir Regla",
                    self.add_rule, COLORS['btn_success'],
                    font_size=11, width=14).pack(side=tk.LEFT, padx=5)
        
        StyledButton(btn_frame, "Eliminar Seleccionada",
                    self.delete_rule, COLORS['btn_stop'],
                    font_size=11, width=18).pack(side=tk.LEFT, padx=5)
        
        StyledButton(btn_frame, "Importar",
                    self.import_vocab, COLORS['btn_reset'],
                    font_size=11, width=12).pack(side=tk.LEFT, padx=5)
        
        StyledButton(btn_frame, "Exportar",
                    self.export_vocab, COLORS['btn_reset'],
                    font_size=11, width=12).pack(side=tk.LEFT, padx=5)
        
        StyledButton(btn_frame, "Cerrar",
                    self.close, '#444c56',
                    hover_color='#5d6774',
                    font_size=11, width=12).pack(side=tk.RIGHT, padx=5)
    
    def load_vocabulary(self):
        """Carga el vocabulario en el treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        vocab = self.vocab.get_vocabulary()
        for incorrect, correct in vocab.items():
            self.tree.insert('', tk.END, values=(incorrect, correct))
    
    def add_rule(self):
        """Añade una nueva regla"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Añadir Regla")
        dialog.geometry("500x200")
        dialog.configure(bg=COLORS['bg_primary'])
        dialog.transient(self.window)
        dialog.grab_set()
        
        frame = tk.Frame(dialog, bg=COLORS['bg_primary'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(frame, text="Texto incorrecto:",
                bg=COLORS['bg_primary'],
                fg=COLORS['text_primary'],
                font=('Segoe UI', 11)).grid(row=0, column=0, padx=5, pady=8, sticky='w')
        
        incorrect_entry = tk.Entry(frame, width=40, font=('Segoe UI', 11),
                                  bg=COLORS['bg_secondary'],
                                  fg=COLORS['text_primary'],
                                  insertbackground=COLORS['text_primary'],
                                  relief=tk.FLAT,
                                  highlightbackground=COLORS['border'],
                                  highlightthickness=1)
        incorrect_entry.grid(row=0, column=1, padx=5, pady=8)
        
        tk.Label(frame, text="Texto correcto:",
                bg=COLORS['bg_primary'],
                fg=COLORS['text_primary'],
                font=('Segoe UI', 11)).grid(row=1, column=0, padx=5, pady=8, sticky='w')
        
        correct_entry = tk.Entry(frame, width=40, font=('Segoe UI', 11),
                                bg=COLORS['bg_secondary'],
                                fg=COLORS['text_primary'],
                                insertbackground=COLORS['text_primary'],
                                relief=tk.FLAT,
                                highlightbackground=COLORS['border'],
                                highlightthickness=1)
        correct_entry.grid(row=1, column=1, padx=5, pady=8)
        
        def save():
            incorrect = incorrect_entry.get().strip()
            correct = correct_entry.get().strip()
            if incorrect and correct:
                self.vocab.add_rule(incorrect, correct)
                self.load_vocabulary()
                dialog.destroy()
        
        StyledButton(frame, "Guardar", save, COLORS['btn_success'],
                    font_size=11, width=15).grid(row=2, column=0, columnspan=2, pady=15)
        
        incorrect_entry.focus()
    
    def delete_rule(self):
        """Elimina la regla seleccionada"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])
            incorrect = item['values'][0]
            if messagebox.askyesno("Confirmar", f"¿Eliminar regla '{incorrect}'?"):
                self.vocab.remove_rule(incorrect)
                self.load_vocabulary()
    
    def import_vocab(self):
        """Importa vocabulario desde archivo"""
        filename = filedialog.askopenfilename(filetypes=[('JSON', '*.json')])
        if filename:
            if self.vocab.import_vocabulary(filename):
                self.load_vocabulary()
                messagebox.showinfo("Éxito", "Vocabulario importado correctamente")
            else:
                messagebox.showerror("Error", "No se pudo importar el vocabulario")
    
    def export_vocab(self):
        """Exporta vocabulario a archivo"""
        filename = filedialog.asksaveasfilename(defaultextension=".json",
                                               filetypes=[('JSON', '*.json')])
        if filename:
            if self.vocab.export_vocabulary(filename):
                messagebox.showinfo("Éxito", "Vocabulario exportado correctamente")
            else:
                messagebox.showerror("Error", "No se pudo exportar el vocabulario")
    
    def close(self):
        """Cierra la ventana"""
        self.window.destroy()
