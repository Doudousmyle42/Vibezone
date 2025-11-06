# config.py (CODE CORRIGÉ)

import os

# Définition de la classe de configuration unique
class Config:
    # Clé secrète (utilisée pour les sessions et les formulaires)
    SECRET_KEY = os.getenv('SECRET_KEY', 'votre_cle_par_defaut_si_non_specifiee')
    
    # 1. Configuration de la Base de Données (ESSENTIEL)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///vibe_zone.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 2. Configuration des Photos de Profil (ajouts)
    # Le chemin complet doit utiliser app.root_path pour être sûr
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'static/profile_pics')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}