from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate  # ✅ Important
from flask_cors import CORS
from dotenv import load_dotenv
import os

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    load_dotenv()

    app = Flask(__name__, template_folder='templates', static_folder='static')
    CORS(app)

    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")
    app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    migrate.init_app(app, db)  # ✅ Connect Flask-Migrate

    from .routes import main
    app.register_blueprint(main)

    return app
