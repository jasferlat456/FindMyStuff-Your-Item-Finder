from flask import Flask, session
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer
from werkzeug.security import generate_password_hash
import os
from models import db, User, Notification
from routes import register_routes

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a_very_secure_secret_key_for_sessions_2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/findmystuff'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Mail Config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'jasfer.ly1@gmail.com'
app.config['MAIL_PASSWORD'] = 'xuiyzvzuwifuscnv'
app.config['MAIL_DEFAULT_SENDER'] = 'jasfer.ly1@gmail.com'

db.init_app(app)
mail = Mail(app)
s = URLSafeTimedSerializer(app.config['SECRET_KEY'])

# Register all routes from routes.py
register_routes(app, mail, s)

@app.context_processor
def inject_notifications():
    if 'user_id' in session:
        count = Notification.query.filter_by(user_id=session['user_id'], is_read=False).count()
        return dict(unread_count=count)
    return dict(unread_count=0)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='jasfer.ly1@gmail.com',
                password=generate_password_hash('Your_admin123', method='pbkdf2:sha256'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
    app.run(debug=True)