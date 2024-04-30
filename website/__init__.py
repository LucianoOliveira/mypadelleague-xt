from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
import re

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'Hello From Hell! :D'

    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/') 

    from .models import Players
    from datetime import date
    from datetime import datetime, timedelta
    from sqlalchemy.sql import func

    with app.app_context():
        db.create_all()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return Players.query.get(int(id))
    
    def calculate_age(birthdate):
        today = date.today()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age
    
    def display_short_name(long_name):
        match = re.search(r'"(.*?)"', long_name)
        if match:
            short_name= match.group(1)
        else:
            short_name = long_name
        return short_name
    
    # Make the calculate_age function accessible to the entire application
    app.jinja_env.globals.update(calculate_age=calculate_age)
    # Make the display_short_name function accessible to the entire application
    app.jinja_env.globals.update(display_short_name=display_short_name)

    return app