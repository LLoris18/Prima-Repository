import os.path
from flask import Flask, redirect, url_for, session
from flask_bootstrap import Bootstrap
from flask import render_template, request, flash
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail, Message
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager, login_user, login_required, current_user, logout_user
from email_validator import validate_email, EmailNotValidError
from flask_wtf.csrf import CSRFProtect
import jwt
import datetime

# Inizializzazione dell'app Flask
load_dotenv('credenziali.env')
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = 'your_app_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Aggiunto per evitare un warning
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)
csrf = CSRFProtect(app)
# Configurazione per il servizio email
app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'ff3832ccdebe56'
app.config['MAIL_PASSWORD'] = '88122cc551c0ef'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


# Definizione dei modelli del database
class Ruolo(db.Model):
    __tablename__ = 'ruoli'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(64), unique=True)
    utenti = db.relationship('Utente', backref='ruolo')

class Utente(UserMixin, db.Model):
    __tablename__ = 'utenti'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    id_ruolo = db.Column(db.Integer, db.ForeignKey('ruoli.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False, nullable=False)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @login_manager.user_loader
    def load_user(user_id):
        return Utente.query.get(int(user_id))


# Altri modelli per i form
class NameForm(FlaskForm):
    name = StringField('Come ti chiami?', validators=[DataRequired()])
    submit = SubmitField('Invia')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Ricorda l\'accesso')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

# Routes e Views
@app.route('/', methods=['GET', 'POST'])
def index():
    form = NameForm()
    if form.validate_on_submit():
        utente = Utente.query.filter_by(username=form.name.data).first()
        if utente is None:
            utente = Utente(username=form.name.data)
            db.session.add(utente)
            db.session.commit()
            session['known'] = False
        else:
            session['known'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('index'))
    return render_template('user1.html', form=form, name=session.get('name'), known=session.get('known', False))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Creazione di un nuovo utente
        new_user = Utente(username=username, email=email, password=password)

        # Salvataggio nel database
        db.session.add(new_user)
        db.session.commit()

        # Generazione del token JWT
        token = jwt.encode({'email': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)},
                           app.config['SECRET_KEY'], algorithm='HS256')

        # Invio dell'email di conferma
        msg = Message('Conferma il tuo account',
                      sender='your_email@example.com',
                      recipients=[email])
        msg.body = f'Clicca sul seguente link per confermare il tuo account: {request.url_root}confirm/{token}'
        #mail.send(msg)

        flash('Ti abbiamo inviato un link di conferma. Controlla la tua email.', 'info')
        return redirect(url_for('index'))

    return render_template('register.html', form=form)
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        try:
            validate_email(form.email.data)
        except EmailNotValidError as e:
            flash('Email non valida')
        utente = Utente.query.filter_by(email=form.email.data).first()
        if utente is not None and utente.verify_password(form.password.data):
            login_user(utente, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Email o password non validi')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sei stato scollegato dal sito')
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.drop_all()
        db.create_all()

    app.run(debug=True)
