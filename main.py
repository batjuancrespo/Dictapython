# Dictado Radiológico Python
# Aplicación de escritorio para dictado médico con IA

import os
import sys

# Asegurar que estamos en el directorio correcto
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

os.chdir(application_path)

from gui import DictadoRadiologicoApp
import tkinter as tk

def main():
    root = tk.Tk()
    app = DictadoRadiologicoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
