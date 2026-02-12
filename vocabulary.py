# Módulo de gestión de vocabulario
import json
import os
from config import VOCABULARY_FILE

class VocabularyManager:
    def __init__(self):
        self.vocabulary = {}
        self.file_path = VOCABULARY_FILE
        self.load_vocabulary()
    
    def load_vocabulary(self):
        """Carga el vocabulario desde el archivo JSON"""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self.vocabulary = json.load(f)
            except Exception as e:
                print(f"Error cargando vocabulario: {e}")
                self.vocabulary = {}
        else:
            self.vocabulary = {}
    
    def save_vocabulary(self):
        """Guarda el vocabulario en el archivo JSON"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self.vocabulary, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error guardando vocabulario: {e}")
            return False
    
    def add_rule(self, incorrect, correct):
        """Añade una nueva regla de corrección"""
        if incorrect and correct:
            # Guardar en minúsculas como en la versión web
            self.vocabulary[incorrect.lower()] = correct
            return self.save_vocabulary()
        return False
    
    def remove_rule(self, incorrect):
        """Elimina una regla de corrección"""
        if incorrect.lower() in self.vocabulary:
            del self.vocabulary[incorrect.lower()]
            return self.save_vocabulary()
        return False
    
    def get_vocabulary(self):
        """Devuelve el vocabulario actual"""
        return self.vocabulary.copy()
    
    def export_vocabulary(self, filepath):
        """Exporta el vocabulario a un archivo"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.vocabulary, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error exportando vocabulario: {e}")
            return False
    
    def import_vocabulary(self, filepath):
        """Importa vocabulario desde un archivo"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                imported = json.load(f)
                # Fusionar con el vocabulario existente
                self.vocabulary.update(imported)
                return self.save_vocabulary()
        except Exception as e:
            print(f"Error importando vocabulario: {e}")
            return False
    
    def clear_vocabulary(self):
        """Limpia todo el vocabulario"""
        self.vocabulary = {}
        return self.save_vocabulary()
