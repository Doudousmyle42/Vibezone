# forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
# DateField : utilisable sous WTForms 3+, fallback pour anciennes versions
try:
    from wtforms.fields import DateField
except ImportError:
    from wtforms.fields.html5 import DateField

from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError

class RegistrationForm(FlaskForm):
    # Authentification
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Mot de passe', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirmer le mot de passe', validators=[DataRequired(), EqualTo('password', message='Les mots de passe doivent correspondre')])
    
    # Profil
    first_name = StringField('Prénom', validators=[DataRequired(), Length(min=2, max=60)])
    date_of_birth = DateField('Date de naissance (AAAA-MM-JJ)', format='%Y-%m-%d', validators=[DataRequired()])
    city = StringField('Ville', validators=[DataRequired(), Length(max=100)])
    
    # Icebreakers
    icebreaker_1 = StringField('Mon son préféré est...', validators=[Length(max=140)])
    icebreaker_2 = StringField('Je suis obsédé par...', validators=[Length(max=140)])
    icebreaker_3 = StringField('Mon pire talent caché est...', validators=[Length(max=140)])

    submit = SubmitField("C'est parti ! 💖")

    # Validation personnalisée — import local pour éviter circular import
    def validate_email(self, email):
        from models import User
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Cet email est déjà utilisé. Veuillez en choisir un autre.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Mot de passe', validators=[DataRequired()])
    remember = BooleanField('Se souvenir de moi')
    submit = SubmitField('Connexion ➡️')