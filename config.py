# config.py

import os

class Config:
    # Clé secrète (utilisée pour les sessions et les formulaires)
    SECRET_KEY = os.getenv('SECRET_KEY', 'votre_cle_par_defaut_si_non_specifiee')
    
    # Configuration de la Base de Données
    # Utilisation de SQLite pour le MVP, stocké dans un fichier au niveau racine
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///vibe_zone.db')
    
    # Désactiver le suivi de modification pour économiser des ressources (facultatif mais recommandé)
    SQLALCHEMY_TRACK_MODIFICATIONS = False