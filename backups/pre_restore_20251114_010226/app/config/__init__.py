from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os

db = SQLAlchemy()

def create_app(config_name='default'):
    app = Flask(__name__)
    load_dotenv()  # Load .env file
    app.config.from_object(config[config_name])
    db.init_app(app)
    return app
