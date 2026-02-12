# Módulo de procesamiento de texto
import re

class TextProcessor:
    def __init__(self):
        self.punctuation_map = {
            'punto y aparte': '.\n',
            'punto y seguido': '.',
            'coma': ',',
            'punto': '.',
            'nuevalinea': '\n',
            'nueva linea': '\n',
            'dos puntos': ':',
            'dospuntos': ':'
        }
    
    def process_text(self, text, vocabulary=None):
        """Procesa el texto completo aplicando todas las reglas"""
        if not text:
            return ""
        
        # 1. Limpiar artefactos
        text = self.cleanup_artifacts(text)
        
        # 2. Aplicar reglas de puntuación
        text = self.apply_punctuation_rules(text)
        
        # 3. Limpiar puntuación duplicada
        text = self.cleanup_double_punctuation(text)
        
        # 4. Capitalizar oraciones
        text = self.capitalize_sentences(text)
        
        # 5. Aplicar correcciones de vocabulario
        if vocabulary:
            text = self.apply_vocabulary_corrections(text, vocabulary)
        
        # 6. Normalizar espacios en paréntesis
        text = self.normalize_parentheses_spacing(text)
        
        return text.strip()
    
    def cleanup_artifacts(self, text):
        """Limpia artefactos del texto"""
        if not text:
            return text
        
        text = text.strip()
        
        # Eliminar comillas al inicio y final si están pareadas
        if text.startswith('"') and text.endswith('"') and len(text) > 2:
            text = text[1:-1].strip()
        
        # Eliminar espacios múltiples
        text = re.sub(r' +', ' ', text)
        
        return text
    
    def apply_punctuation_rules(self, text):
        """Aplica las reglas de puntuación"""
        if not text:
            return text
        
        processed = text
        
        # Ordenar claves por longitud descendente para evitar reemplazos parciales
        sorted_keys = sorted(self.punctuation_map.keys(), key=len, reverse=True)
        
        for key in sorted_keys:
            # Crear regex que busca la palabra completa (case insensitive)
            regex = re.compile(r'\b' + re.escape(key) + r'\b', re.IGNORECASE)
            processed = regex.sub(self.punctuation_map[key], processed)
        
        return processed
    
    def cleanup_double_punctuation(self, text):
        """Limpia puntuación duplicada"""
        if not text:
            return text
        
        # Reemplazar múltiples puntuaciones seguidas
        def replace_punctuation(match):
            punct = match.group(1)
            if '.\n' in punct:
                return '.\n'
            elif '\n' in punct:
                return '\n'
            elif '!' in punct:
                return '!'
            elif '?' in punct:
                return '?'
            elif '.' in punct:
                return '.'
            elif ':' in punct:
                return ':'
            elif ';' in punct:
                return ';'
            elif ',' in punct:
                return ','
            return ' '
        
        # Buscar secuencias de puntuación
        text = re.sub(r'([.,:;!?\n][\s.,:;!?\n]*)', replace_punctuation, text)
        
        # Eliminar espacios antes de puntuación
        text = re.sub(r'\s+([.,:;!?\n])', r'\1', text)
        
        # Asegurar espacio después de puntuación (excepto salto de línea)
        text = re.sub(r'([.,:;!?])([a-zA-ZáéíóúüñÁÉÍÓÚÑ])', r'\1 \2', text)
        
        # Normalizar saltos de línea
        text = re.sub(r'\s*\n\s*', '\n', text)
        
        # Eliminar espacios múltiples
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def capitalize_sentences(self, text):
        """Capitaliza el inicio de cada oración"""
        if not text:
            return text
        
        # Primera letra del texto
        text = text[0].upper() + text[1:] if len(text) > 0 else text
        
        # Después de puntos, signos de exclamación, interrogación o saltos de línea
        def capitalize_after_punct(match):
            punct = match.group(1)
            letter = match.group(2)
            return punct + letter.upper()
        
        text = re.sub(r'([.!?\n]\s*)([a-záéíóúüñ])', capitalize_after_punct, text)
        
        return text
    
    def apply_vocabulary_corrections(self, text, vocabulary):
        """Aplica correcciones del vocabulario personalizado"""
        if not text or not vocabulary:
            return text
        
        processed = text
        
        # Ordenar por longitud descendente para evitar reemplazos parciales
        sorted_keys = sorted(vocabulary.keys(), key=len, reverse=True)
        
        for error_key in sorted_keys:
            correct_value = vocabulary[error_key]
            try:
                # Escapar caracteres especiales en la clave
                escaped_key = re.escape(error_key)
                regex = re.compile(r'\b' + escaped_key + r'\b', re.IGNORECASE)
                processed = regex.sub(correct_value, processed)
            except re.error as e:
                print(f"Error en regex para '{error_key}': {e}")
        
        return processed
    
    def normalize_parentheses_spacing(self, text):
        """Normaliza espacios alrededor de paréntesis"""
        if not text:
            return text
        
        # Eliminar espacios después de ( y antes de )
        text = re.sub(r'\(\s+', '(', text)
        text = re.sub(r'\s+\)', ')', text)
        
        # Asegurar espacio antes de ( si no hay coma
        text = re.sub(r'(?<!,)\s*\(', ' (', text)
        
        # Eliminar espacio entre ) y puntuación
        text = re.sub(r'\)\s*([.,:;!?])', r')\1', text)
        
        return text
    
    def format_time(self, seconds):
        """Formatea segundos a MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
