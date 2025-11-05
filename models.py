# models.py

# IMPORTANT : L'objet 'db' sera importé depuis 'app'
from extensions import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    first_name = db.Column(db.String(60), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    vibe_tags = db.Column(db.String(255), nullable=True)
    icebreaker_1 = db.Column(db.String(140), nullable=True)
    icebreaker_2 = db.Column(db.String(140), nullable=True)
    icebreaker_3 = db.Column(db.String(140), nullable=True)
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
    
# models.py (ajouts)

# ... (La classe User est au-dessus) ...

class Swipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # L'ID de l'utilisateur qui effectue l'action (le "swiper")
    swiper_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # L'ID de l'utilisateur qui est vu (le "swiped")
    swiped_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # L'action : True pour "Like", False pour "Dislike"
    liked = db.Column(db.Boolean, nullable=False)
    
    # Quand l'action a eu lieu
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        action = "Liked" if self.liked else "Disliked"
        return f'<Swipe {self.swiper_id} {action} {self.swiped_id}>'


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # L'ID du premier utilisateur dans le match
    user1_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # L'ID du second utilisateur dans le match
    user2_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Quand le match a été créé
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        return f'<Match {self.user1_id} and {self.user2_id}>'