# app.py

from flask import Flask, render_template, url_for, flash, redirect, request
from dotenv import load_dotenv
from config import Config
from extensions import db
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import os
import secrets
from PIL import Image
from sqlalchemy import or_   # <-- ajouté
from datetime import date
import json


# Supprimé : imports précoces de models/forms pour éviter la circularité


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
from models import User, Swipe, Match, Message  # importe les modèles maintenant que db est initialisé
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
    
# À ajouter dans app.py après la route /feed

# app.py (ajouts)

# ... (vos autres routes sont ici : /login, /register, /feed) ...

@app.route('/swipe/<int:swiped_id>/<action>')
@login_required
def swipe(swiped_id, action):
    """
    Enregistre l'action de swipe (like/dislike) et vérifie s'il y a un match.
    """
    
    # 1. Vérifications de sécurité de base
    if not action in ['like', 'dislike']:
        flash("Action non valide.", "danger")
        return redirect(url_for('feed'))

    if swiped_id == current_user.id:
        flash("Vous ne pouvez pas vous swiper vous-même !", "warning")
        return redirect(url_for('feed'))
        
    # 2. Vérifier si l'utilisateur a déjà swipé ce profil
    existing_swipe = Swipe.query.filter_by(
        swiper_id=current_user.id, 
        swiped_id=swiped_id
    ).first()
    
    if existing_swipe:
        flash("Vous avez déjà vu ce profil.", "info")
        return redirect(url_for('feed'))

    # 3. Déterminer la valeur de 'liked'
    user_liked = True if action == 'like' else False

    # 4. Enregistrer le nouveau swipe dans la base de données
    new_swipe = Swipe(
        swiper_id=current_user.id,
        swiped_id=swiped_id,
        liked=user_liked
    )
    db.session.add(new_swipe)
    
    # 5. --- LOGIQUE DE MATCH ---
    # Si l'utilisateur actuel a "liké" (user_liked == True)
    if user_liked:
        # On vérifie si l'AUTRE personne (swiped_id) a DÉJÀ "liké" l'utilisateur actuel (current_user.id)
        mutual_like = Swipe.query.filter_by(
            swiper_id=swiped_id, 
            swiped_id=current_user.id,
            liked=True
        ).first()
        
        if mutual_like:
            # C'EST UN MATCH ! (ou "It's a Vibe!")
            
            # On vérifie si le match n'existe pas déjà (double sécurité)
            existing_match = Match.query.filter(
                (Match.user1_id == current_user.id) & (Match.user2_id == swiped_id) |
                (Match.user1_id == swiped_id) & (Match.user2_id == current_user.id)
            ).first()

            if not existing_match:
                # Créer le nouveau match
                new_match = Match(
                    user1_id=current_user.id,
                    user2_id=swiped_id
                )
                db.session.add(new_match)
                
                # Récupérer le nom de la personne matchée pour le message flash
                matched_user = User.query.get(swiped_id)
                flash(f"C'est un Vibe ! Vous avez matché avec {matched_user.first_name}.", "success")

    # 6. Valider les changements dans la base de données
    db.session.commit()
    
    # 7. Rediriger vers le feed pour le prochain profil
    return redirect(url_for('feed'))

# À ajouter dans app.py après la route /swipe

@app.route('/matches')
@login_required
def matches():
    """
    Affiche tous les matches de l'utilisateur connecté.
    """
    # Récupérer tous les matches où l'utilisateur est impliqué
    user_matches = Match.query.filter(
        db.or_(
            Match.user1_id == current_user.id,
            Match.user2_id == current_user.id
        )
    ).order_by(Match.timestamp.desc()).all()
    
    # Créer une liste des profils matchés avec leurs infos
    matched_users = []
    for match in user_matches:
        # Déterminer qui est l'autre utilisateur
        other_user_id = match.user2_id if match.user1_id == current_user.id else match.user1_id
        other_user = db.session.get(User, other_user_id)
        
        if other_user:
            matched_users.append({
                'user': other_user,
                'match_date': match.timestamp
            })
    
    return render_template('matches.html', matches=matched_users, total=len(matched_users))
    
    # 6. Sauvegarder en base de données
    db.session.commit()
    
    # 7. Messages flash selon le résultat
    if is_match:
        flash(f'🎉 C\'est un MATCH avec {swiped_user.first_name} ! Vous pouvez maintenant discuter.', 'success')
        # Optionnel : rediriger vers la page de match ou de messagerie
        # return redirect(url_for('matches'))
    elif liked:
        flash(f'💖 Tu as liké {swiped_user.first_name} !', 'info')
    else:
        flash(f'Profil passé. Suivant !', 'info')
    
    # 8. Redirection vers le prochain profil
    return redirect(url_for('feed'))


@app.route('/users/<int:user_id>')
@login_required
def user_profile(user_id):   # <--- renommé de 'profile' en 'user_profile'
    user = User.query.get_or_404(user_id)
    return render_template('users/profil.html', user=user)

# Edition du profil — nom/fonction et URL différents pour éviter conflit
@app.route('/profile/<int:user_id>/edit', endpoint='profile_edit', methods=['GET', 'POST'])
@login_required
def profile_edit(user_id):
    user = User.query.get_or_404(user_id)
    # ...gestion du formulaire d'édition...
    return render_template('users/update_profile.html', user=user)

@app.route('/inbox')
@login_required
def inbox():
    """
    Affiche la liste de tous les matchs (conversations) de l'utilisateur.
    """
    
    # 1. Trouver tous les "Match" où l'utilisateur actuel est user1 OU user2
    # 
    all_matches = Match.query.filter(
        or_(Match.user1_id == current_user.id, Match.user2_id == current_user.id)
    ).all()
    
    # 2. Extraire les ID des personnes avec qui l'utilisateur a matché
    matched_user_ids = []
    for match in all_matches:
        if match.user1_id == current_user.id:
            # Si je suis user1, je veux l'ID de user2
            matched_user_ids.append(match.user2_id)
        else:
            # Si je suis user2, je veux l'ID de user1
            matched_user_ids.append(match.user1_id)
            
    # 3. Récupérer les objets User correspondants à ces ID
    # On utilise .in_(...) pour une requête efficace
    if matched_user_ids:
        matches = User.query.filter(User.id.in_(matched_user_ids)).all()
    else:
        matches = [] # Pas encore de matchs

    return render_template('messaging/inbox.html', matches=matches)

@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    from forms import MessageForm
    form = MessageForm()
    """
    Page de conversation individuelle avec un autre utilisateur.
    """
    
    # 1. Récupérer l'utilisateur à qui on veut parler
    recipient = User.query.get_or_404(user_id)
    
    # 2. SÉCURITÉ : Vérifier s'il y a un match entre l'utilisateur actuel et le destinataire
    match = Match.query.filter(
        or_(
            (Match.user1_id == current_user.id) & (Match.user2_id == user_id),
            (Match.user1_id == user_id) & (Match.user2_id == current_user.id)
        )
    ).first()
    
    if not match:
        # S'il n'y a pas de match, interdire l'accès
        flash("Vous ne pouvez discuter qu'avec vos matchs.", "danger")
        return redirect(url_for('inbox'))

    # 3. Initialiser le formulaire
    form = MessageForm()
    
    # 4. Gérer l'envoi de message (POST)
    if form.validate_on_submit():
        new_message = Message(
            sender_id=current_user.id,
            recipient_id=user_id,
            body=form.body.data
        )
        db.session.add(new_message)
        db.session.commit()
        # Rediriger vers la même page pour afficher le nouveau message (Pattern Post-Redirect-Get)
        return redirect(url_for('chat', user_id=user_id))
    
    # 5. Récupérer l'historique des messages (GET)
    messages = Message.query.filter(
        or_(
            # Messages de moi à lui
            (Message.sender_id == current_user.id) & (Message.recipient_id == user_id),
            # Messages de lui à moi
            (Message.sender_id == user_id) & (Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all() # Trier par le plus ancien

    return render_template('messaging/chat.html', 
                                recipient=recipient, 
                                form=form, 
                                messages=messages)

# app.py (ajouts)

# ... (autres routes) ...

@app.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)

    # calcule l'âge côté serveur
    age = None
    if user.date_of_birth:
        dob = user.date_of_birth
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

    # si vibe_tags stockées en JSON string, désérialiser en liste
    vibe_tags = []
    if user.vibe_tags:
        try:
            vibe_tags = json.loads(user.vibe_tags)
        except Exception:
            # si stockage simple "tag1,tag2"
            vibe_tags = [t.strip() for t in (user.vibe_tags or "").split(',') if t.strip()]

    return render_template('users/profil.html', user=user, age=age, vibe_tags=vibe_tags)

# Fonction pour vérifier l'extension du fichier
def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# Fonction pour sauvegarder la photo (avec redimensionnement)
def save_picture(form_picture):
    # 1. Générer un nom de fichier aléatoire pour éviter les conflits
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename) # Extrait l'extension
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    # 2. Redimensionner l'image (pour économiser de l'espace et uniformiser)
    output_size = (400, 400) # Taille idéale pour une carte de profil
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    
    # 3. Sauvegarder l'image redimensionnée
    i.save(picture_path)

    return picture_fn # Retourne le nom de fichier sauvegardé

@app.route('/settings/picture', methods=['GET', 'POST'])
@login_required
def update_picture():
    from forms import UpdateProfileForm
    form = UpdateProfileForm()
    
    if form.validate_on_submit():
        if form.picture.data and allowed_file(form.picture.data.filename):
            
            # 1. Sauvegarder l'image
            picture_file = save_picture(form.picture.data)
            
            # 2. Mettre à jour le champ image_file de l'utilisateur
            current_user.image_file = picture_file
            
            db.session.commit()
            flash('Votre photo de profil a été mise à jour !', 'success')
            return redirect(url_for('profile', user_id=current_user.id))
            
        elif form.picture.data and not allowed_file(form.picture.data.filename):
            flash('Erreur : Type de fichier non supporté.', 'danger')
            
    # L'URL de la photo actuelle
    image_url = url_for('static', filename='profile_pics/' + current_user.image_file)
    
    return render_template('users/update_picture.html', title='Photo de Profil', form=form, image_url=image_url)

if __name__ == '__main__':
    app.run(debug=True)