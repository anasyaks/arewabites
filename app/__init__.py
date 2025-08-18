import os
from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from datetime import datetime
from app.config import Config
from flask_socketio import SocketIO
import cloudinary

# Initialize extensions
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()
migrate = Migrate()
socketio = SocketIO()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app)
    
    # Cloudinary Configuration
    if all([app.config['CLOUDINARY_CLOUD_NAME'], app.config['CLOUDINARY_API_KEY'], app.config['CLOUDINARY_API_SECRET']]):
        cloudinary.config(
            cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
            api_key=app.config['CLOUDINARY_API_KEY'],
            api_secret=app.config['CLOUDINARY_API_SECRET']
        )
    else:
        print("Cloudinary credentials are not set. File uploads will fail.")

    @app.context_processor
    def inject_globals():
        current_vendor = None
        if 'vendor_id' in session:
            from app.models import Vendor
            current_vendor = db.session.get(Vendor, session.get('vendor_id'))
        return {
            'now': datetime.utcnow(),
            'current_vendor': current_vendor
        }

    from app.routes import main
    app.register_blueprint(main)

    return app

from app import models
import app.events