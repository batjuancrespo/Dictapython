# Módulo del Juanizador (Asistente de Informes)
import json
import re
from config import ANATOMICAL_CATEGORIES
from transcription import TranscriptionService

class JuanizadorService:
    def __init__(self):
        self.categories = ANATOMICAL_CATEGORIES
        self.transcription_service = TranscriptionService()
        self.categorized_findings = {}
    
    def generate_technique_text(self, tech, tac_scope=None, rm_type=None, contrast=False, phases=None):
        """Genera el texto de la técnica"""
        if tech == 'eco':
            return "Exploración ecográfica con sonda multifrecuencia."
        
        if tech == 'rm':
            contrast_text = " y estudio dinámico tras la administración endovenosa de contraste" if contrast else ""
            
            if rm_type == 'hepatica':
                return f"Se realiza exploración abdominal con secuencias potenciadas en T1 en fase y fuera de fase, T2 sin y con saturación grasa, difusión{contrast_text}."
            elif rm_type == 'colangio':
                return "Se realiza exploración abdominal con secuencias potenciadas en T1 en fase y fuera de fase, T2 sin y con saturación grasa, estudio dinámico tras la administración endovenosa de contraste completándose la valoración con cortes radiales respecto al colédoco orientados a la valoración de la via biliar."
            elif rm_type == 'entero':
                return "Se realiza exploración abdominal con secuencias potenciadas en T2, difusión y estudio dinámico tras la administración endovenosa de contraste previa distensión de las asas intestinales. Exploración orientada a la valoración de asas de intestino delgado."
            elif rm_type == 'fistulas':
                return "Se realiza exploración pélvica con secuencias potenciadas en T2 sin y con saturación grasa y difusión."
            elif rm_type == 'neo-pelvis':
                return "Se realiza exploración pélvica con secuencias potenciadas en T2 sin y con saturación grasa en los tres planos del espacio, difusión y estudio dinámico tras la administración endovenosa de contraste."
        
        if tech == 'tac':
            scope_map = {
                'toracoabdominal': 'toracoabdominal',
                'torax': 'torácico',
                'abdomen': 'abdominal'
            }
            scope = scope_map.get(tac_scope if tac_scope else '', 'abdominal')
            
            text = f"Se realiza exploración {scope}"
            
            if contrast:
                text += " tras la administración endovenosa de contraste"
                if phases:
                    phases_text = ' y '.join(phases)
                    text += f" con adquisición de imágenes en fase {phases_text}"
            else:
                text += " sin administración endovenosa de contraste"
            
            return text + "."
        
        return ""
    
    def categorize_findings(self, transcript, available_categories, on_status=None):
        """Categoriza los hallazgos usando la IA"""
        if not transcript.strip():
            return None, "No hay hallazgos para categorizar"
        
        if not self.transcription_service.is_available():
            return None, "Servicio de IA no disponible"
        
        try:
            if on_status:
                on_status("Categorizando hallazgos...")
            
            # Filtrar categorías disponibles
            filtered_categories = [cat for cat in self.categories if cat['id'] in available_categories]
            category_names = '\n'.join([f"{cat['id']}. {cat['name']}" for cat in filtered_categories])
            
            prompt = f"""Eres un radiólogo experto. Categoriza los siguientes hallazgos en las categorías disponibles.

Categorías Disponibles:
{category_names}

Hallazgos a Categorizar:
"{transcript}"

Devuelve un objeto JSON con claves de ID de categoría (como strings) y valores como array de hallazgos. 
Incluye solo categorías con hallazgos. Devuelve SOLO el objeto JSON, sin markdown ni explicaciones.

Ejemplo de formato de salida:
{{
  "5": ["Hallazgo 1 del hígado", "Hallazgo 2"],
  "8": ["Hallazgo de riñones"]
}}"""
            
            result, error = self.transcription_service.transcribe_text(prompt)
            
            if error:
                return None, error
            
            if not result:
                return None, "No se recibió respuesta de la IA"
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{[\s\S]*\}', result or '')
            if json_match:
                self.categorized_findings = json.loads(json_match.group())
                return self.categorized_findings, None
            else:
                return None, "No se pudo extraer JSON de la respuesta"
                
        except Exception as e:
            return None, f"Error categorizando: {str(e)}"
    
    def generate_report(self, tech, tac_scope, rm_type, contrast, phases, available_categories, on_status=None):
        """Genera el informe completo"""
        if not self.categorized_findings:
            return None, "Primero debe categorizar los hallazgos"
        
        try:
            if on_status:
                on_status("Generando informe...")
            
            # Generar técnica
            technique_text = self.generate_technique_text(tech, tac_scope, rm_type, contrast, phases)
            
            # Preparar lista de hallazgos
            findings_list = []
            report_categories = [cat for cat in self.categories if cat['id'] in available_categories]
            
            for category in report_categories:
                cat_id = str(category['id'])
                if cat_id in self.categorized_findings and self.categorized_findings[cat_id]:
                    findings_list.append({
                        'category': category['name'],
                        'findings': '. '.join(self.categorized_findings[cat_id])
                    })
            
            # Generar contenido con IA
            modality_instruction = {
                'tac': 'TAC',
                'rm': 'Resonancia Magnética (RM)',
                'eco': 'Ecografía'
            }.get(tech, 'genérica')
            
            prompt = f"""Eres un radiólogo experto. Tu tarea es generar el texto para un informe.
Usa vocabulario de {modality_instruction}.

**Tarea 1: Hallazgos Anormales**
Para cada categoría en esta lista, redacta un párrafo profesional describiendo los hallazgos:
{json.dumps(findings_list, ensure_ascii=False)}

**Tarea 2: Conclusión**
Basado SOLAMENTE en los hallazgos anormales de la lista anterior, genera una conclusión concisa de 2-3 líneas resumiendo lo más importante. Si la lista de hallazgos está vacía, la conclusión debe ser "No se observan alteraciones radiológicas significativas."

**Formato de Salida Obligatorio:**
Devuelve un único objeto JSON con dos claves: "report_paragraphs" y "conclusion".
"report_paragraphs" debe ser un objeto donde cada clave es el nombre de la categoría y el valor es el párrafo que has redactado.
Si la lista de hallazgos anormales está vacía, "report_paragraphs" debe ser un objeto vacío {{}}.

Ejemplo:
{{
  "report_paragraphs": {{
    "Hígado, porta y confluente esplenomesentérico venoso": "Texto del párrafo..."
  }},
  "conclusion": "Texto de la conclusión..."
}}"""
            
            result, error = self.transcription_service.transcribe_text(prompt)
            
            if error:
                return None, error
            
            if not result:
                return None, "No se recibió respuesta de la IA"
            
            # Extraer JSON
            json_match = re.search(r'\{[\s\S]*\}', result or '')
            if json_match:
                ai_content = json.loads(json_match.group())
                
                # Ensamblar informe
                findings_text = ""
                for category in report_categories:
                    cat_name = category['name']
                    if ai_content.get('report_paragraphs', {}).get(cat_name):
                        findings_text += ai_content['report_paragraphs'][cat_name] + '\n'
                    elif category.get('normal'):
                        findings_text += category['normal'] + '\n'
                
                conclusion_text = ai_content.get('conclusion', 'No se observan alteraciones radiológicas significativas.')
                full_report = f"{technique_text}\n\n{findings_text.strip()}\n\n{conclusion_text.strip()}"
                
                return {
                    'technique': technique_text,
                    'findings': findings_text.strip(),
                    'conclusion': conclusion_text.strip(),
                    'full_report': full_report
                }, None
            else:
                return None, "No se pudo extraer JSON del informe"
                
        except Exception as e:
            return None, f"Error generando informe: {str(e)}"
    
    def get_available_categories(self, tech, tac_scope=None, rm_type=None):
        """Devuelve las categorías disponibles según la técnica seleccionada"""
        base_categories = [12, 13]
        categories = []
        
        if tech == 'tac':
            if tac_scope == 'toracoabdominal':
                categories = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11] + base_categories
            elif tac_scope == 'torax':
                categories = [0, 1, 2, 3, 4, 15] + base_categories
            elif tac_scope == 'abdomen':
                categories = [5, 6, 7, 8, 9, 10, 11, 14] + base_categories
        elif tech == 'rm':
            if rm_type in ['hepatica', 'colangio']:
                categories = [5, 6, 7, 8, 10] + base_categories
            else:
                categories = [5, 6, 7, 8, 9, 10, 11] + base_categories
        else:  # Eco
            categories = [5, 6, 7, 8, 9, 10, 11] + base_categories
        
        return categories
