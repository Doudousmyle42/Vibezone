# models.py

# Remplace : from app import db
from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    
    # --- 1. Infos d'Authentification ---
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    
    # --- 2. Infos de Profil ---
    first_name = db.Column(db.String(60), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    
    # NOUVEAU : Champ pour le nom de fichier de la photo principale
    # Stocke le nom du fichier (ex: 'abcdef1234.jpg')
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg') 
    
    # --- 3. Le "Vibe Check" ---
    vibe_tags = db.Column(db.String(255), nullable=True) 
    
    # --- 4. Les "Icebreakers" ---
    icebreaker_1 = db.Column(db.String(140), nullable=True)
    icebreaker_2 = db.Column(db.String(140), nullable=True)
    icebreaker_3 = db.Column(db.String(140), nullable=True)

    # --- 5. Sécurité et Métadonnées ---
    is_verified = db.Column(db.Boolean, default=False) # Badge de vérification (âge/selfie)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    
    # --- Méthodes de sécurité ---

    def set_password(self, password):
        """Hache et stocke le mot de passe."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie le mot de passe haché."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"User('{self.first_name}', '{self.email}')"


class Swipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # L'utilisateur qui swipe
    swiper_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # L'utilisateur qui est swipé
    swiped_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # L'action : True pour "Like", False pour "Dislike"
    liked = db.Column(db.Boolean, nullable=False)
    
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        action = "Liked" if self.liked else "Disliked"
        return f'<Swipe {self.swiper_id} {action} {self.swiped_id}>'


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Les ID des deux utilisateurs (triés pour l'unicité du match)
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Match {self.user1_id} and {self.user2_id}>'


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    body = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Message from {self.sender_id} to {self.recipient_id}>'