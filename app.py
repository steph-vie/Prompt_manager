"""Application principale"""

import os
from flask import Flask
from flask_migrate import Migrate
from config import Config
from models import db
from routes import register_routes


def create_app():
    """
    Initialisation de l'application
    """
    app = Flask(__name__)
    migrate = Migrate()
    app.config.from_object(Config)

    # Création du dossier d'upload
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    if not os.path.exists(app.config['DB_FOLDER']):
        os.makedirs(app.config['DB_FOLDER'])

    db.init_app(app)
    migrate.init_app(app, db)
    register_routes(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    # Creation de l'app
    appli = create_app()
    # Lance l’application Flask en mode debug
    appli.run(debug=True)
