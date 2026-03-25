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
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)), 'batman_images', 'joker.jpg'),
                os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)), 'batman_images', 'batmanneal.jpg'),
            ]
        
        batman_paths = [p for p in batman_paths if os.path.exists(p)]
