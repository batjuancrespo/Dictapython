# Dictado Radiológico Python

Aplicación de escritorio en Python para dictado médico con inteligencia artificial. Es una versión local de la web [Dictado Radiológico](https://batjuancrespo.github.io/dictado-radiologico/) que funciona sin necesidad de conexión a internet (excepto para la transcripción con IA).

## Características

- **Grabación de audio** directamente desde el micrófono (hasta 12 minutos)
- **Transcripción con IA** usando Google Gemini (con fallback a múltiples modelos)
- **Procesamiento de texto** inteligente:
  - Comandos de puntuación: "punto y aparte", "coma", "punto", etc.
  - Capitalización automática de oraciones
  - Corrección de puntuación duplicada
- **Botones de técnica predefinidos** (TAC, RM, Ecografía)
- **Juanizador** - Asistente que categoriza hallazgos y genera informes estructurados
- **Vocabulario personalizado** - Correcciones automáticas de palabras
- **Importar/Exportar** vocabulario

## Requisitos

- Python 3.8 o superior
- Micrófono
- Conexión a internet (solo para la transcripción con IA)
- API Key de Google Gemini (gratis)

## Instalación

1. **Clona o descarga** este repositorio

2. **Instala las dependencias**:
```bash
pip install -r requirements.txt
```

3. **Configura tu API Key**:
   - Copia `.env.example` a `.env`
   - Edita `.env` y añade tu API key de Google Gemini:
```
GEMINI_API_KEY=tu_api_key_aqui
```
   - Obtén una API key gratis en: https://aistudio.google.com/app/apikey

## Uso

### Iniciar la aplicación

```bash
python main.py
```

### Funcionalidades principales

#### 1. Grabar dictado
- Pulsa **"Empezar Dictado"** para iniciar la grabación
- Habla claramente al micrófono
- Usa comandos de voz para puntuación:
  - "punto y aparte" → nueva línea
  - "punto y seguido" → punto
  - "coma" → coma
  - "punto" → punto
- Pulsa **"Pausar"** si necesitas hacer una pausa
- Pulsa **"Detener Dictado"** cuando termines
- El texto transcrito aparecerá automáticamente en el área de informe

#### 2. Seleccionar técnica
- Usa los botones de la columna derecha para insertar textos de técnica predefinidos
- Incluye técnicas de TAC, RM y Ecografía

#### 3. Usar el Juanizador (Asistente de Informes)
- Pulsa **"Juanizar"** para analizar el informe
- Selecciona el tipo de estudio (TAC, RM, Ecografía)
- Configura contraste y fases si aplica
- Pulsa **"Categorizar Hallazgos"** para organizar por categorías anatómicas
- Pulsa **"Generar Informe"** para crear el informe estructurado
- Pulsa **"Transferir a Dictado"** para volver con el informe generado

#### 4. Gestionar vocabulario
- Pulsa **"Vocabulario"** para abrir el gestor
- Añade reglas para corregir palabras automáticamente
- Importa/Exporta tu vocabulario personalizado

#### 5. Otros botones
- **Copiar Todo** - Copia técnica e informe al portapapeles
- **Resetear** - Limpia todo el contenido
- **Subir Audio** - Procesa un archivo de audio existente
- **Reenviar audio** - Reprocesa el último audio grabado

## Estructura del proyecto

```
Dictapython/
├── main.py              # Punto de entrada
├── config.py            # Configuración y constantes
├── gui.py               # Interfaz gráfica
├── audio_recorder.py    # Módulo de grabación
├── transcription.py     # Módulo de transcripción IA
├── text_processor.py    # Procesamiento de texto
├── vocabulary.py        # Gestión de vocabulario
├── juanizador.py        # Asistente de informes
├── requirements.txt     # Dependencias
├── .env.example         # Ejemplo de configuración
└── vocabulario.json     # Vocabulario personalizado (se crea automáticamente)
```

## Solución de problemas

### Error "PyAudio no disponible"
En Windows, instala PyAudio con:
```bash
pip install pipwin
pipwin install pyaudio
```

O descarga el wheel apropiado desde:
https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio

### Error "API Key no configurada"
Asegúrate de:
1. Copiar `.env.example` a `.env`
2. Añadir tu API key de Google Gemini válida
3. Reiniciar la aplicación

### La grabación no funciona
- Verifica que tu micrófono esté conectado
- Verifica que tenga permisos de acceso
- Prueba con un archivo de audio existente con "Subir Audio"

### Errores de transcripción
La aplicación intenta automáticamente con 3 modelos diferentes:
1. gemini-2.5-flash
2. gemini-2.0-flash
3. gemini-2.0-flash-lite

Si todos fallan, verifica tu conexión a internet y tu API key.

## Licencia

Proyecto personal para uso médico radiológico.

## Autor

by JCP (basado en la web original)
