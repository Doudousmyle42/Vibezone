# app.py

from flask import Flask, render_template, url_for, flash, redirect, request
from dotenv import load_dotenv
from config import Config
from extensions import db
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
# Charge les variables d'environnement (y compris SECRET_KEY)
load_dotenv()

# --- INITIALISATION DE L'APPLICATION ET DES EXTENSIONS ---
app = Flask(__name__)
app.config.from_object(Config)

# 1. Initialisation de la Base de Données
db.init_app(app)

# 2. Initialisation de Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."

# --- IMPORTS APRÈS INIT (évite import circulaire) ---
from models import User, Swipe
from forms import RegistrationForm, LoginForm

# --- FONCTION DE CHARGEMENT UTILISATEUR POUR FLASK-LOGIN ---

@login_manager.user_loader
def load_user(user_id):
    """Indique à Flask-Login comment recharger un utilisateur."""
    return db.session.get(User, int(user_id))

# --- ROUTES DE BASE ---

@app.route('/')
def home():
    slogan = "Plus que des likes, des connexions réelles."
    return render_template('home.html', slogan=slogan)

@app.route('/about')
def about():
    return render_template('about.html')

# --- ROUTES D'AUTHENTIFICATION ---

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            date_of_birth=form.date_of_birth.data,
            city=form.city.data,
            icebreaker_1=form.icebreaker_1.data,
            icebreaker_2=form.icebreaker_2.data,
            icebreaker_3=form.icebreaker_3.data,
        )
        # Hachage et stockage du mot de passe
        user.set_password(form.password.data) 
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Bienvenue à bord, {form.first_name.data} ! Votre compte est créé. Connectez-vous maintenant.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html', title='Inscription', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        # Vérification du mot de passe
        if user and user.check_password(form.password.data):
            # Connexion réussie
            login_user(user, remember=form.remember.data)
            
            # Gestion de la redirection après connexion
            next_page = request.args.get('next')
            flash('Connexion réussie. Bienvenue de retour !', 'success')
            return redirect(next_page or url_for('home'))
        else:
            flash('Échec de la connexion. Veuillez vérifier votre email et mot de passe.', 'danger')

    return render_template('auth/login.html', title='Connexion', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('Vous êtes déconnecté. À bientôt !', 'info')
    return redirect(url_for('home'))


# --- ROUTE PROTÉGÉE /feed (unique, logique de swipe) ---
@app.route('/feed')
@login_required
def feed():
    """
    Affiche le prochain profil disponible pour le swipe.
    """
    # 1. Récupérer les ID de tous les utilisateurs que l'utilisateur actuel a DÉJÀ swipé.
    swiped_users_tuples = db.session.query(Swipe.swiped_id).filter_by(swiper_id=current_user.id).all()
    swiped_user_ids = [user_id for (user_id,) in swiped_users_tuples]
    swiped_user_ids.append(current_user.id)
    
    # 2. Trouver le premier utilisateur qui n'est pas dans la liste
    profile_to_show = User.query.filter(User.id.notin_(swiped_user_ids)).first()

    # 3. Afficher le profil ou la page "vide"
    if profile_to_show:
        return render_template('feed/feed.html', user=profile_to_show)
    else:
        return render_template('feed/feed_empty.html')


if __name__ == '__main__':
    app.run(debug=True)