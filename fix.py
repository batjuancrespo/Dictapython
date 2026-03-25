# Script para corregir error de sintaxis en gui.py
import os

# Leer archivo
with open('gui.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Corregir error: doble paréntesis en batman_folder
old1 = "batman_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'batman_images')"
new1 = "batman_folder = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'batman_images')".replace('__file__))), ', '__file__)), '

content = content.replace(old1, new1)

# Corregir error: doble paréntesis en extend
old2 = "batman_paths.extend(glob.glob(os.path.join(batman_folder, ext)))"
new2 = "batman_paths.extend(glob.glob(os.path.join(batman_folder, ext)))".replace('ext)))', 'ext))')

content = content.replace(old2, new2)

# Escribir archivo corregido
with open('gui.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Archivo corregido!")
