from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email

import jwt
import datetime

app = Flask(__name__)
csrf = CSRFProtect(app)
Bootstrap(app)

# Configurazione del database (nella tua app dovresti utilizzare un database reale, ad esempio PostgreSQL)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
db = SQLAlchemy(app)

# Configurazione di Flask-Mail
app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = 'ff3832ccdebe56'
app.config['MAIL_PASSWORD'] = '88122cc551c0ef'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)

# Chiave segreta per la generazione del token JWT
app.config['SECRET_KEY'] = 'your_secret_key'

# Modello dei dati dell'utente
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    confirmed = db.Column(db.Boolean, default=False)

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

# Rotte
@app.route('/')
def home():
    return "Benvenuto al tuo sito di registrazione!"

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data

        # Creazione di un nuovo utente
        new_user = User(username=username, email=email, password=password)

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
        mail.send(msg)

        flash('Ti abbiamo inviato un link di conferma. Controlla la tua email.', 'info')
        return redirect(url_for('home'))

    return render_template('register.html', form=form)
@app.route('/confirm/<token>')
def confirm(token):
    try:
        email = jwt.decode(token, app.config['SECRET_KEY'])['email']
        user = User.query.filter_by(email=email).first()
        if user:
            user.confirmed = True
            db.session.commit()
            flash('Il tuo account è stato confermato con successo!', 'success')
        else:
            flash('Token non valido o scaduto.', 'danger')
    except:
        flash('Token non valido o scaduto.', 'danger')

    return redirect(url_for('home'))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
