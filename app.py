import os
from flask import Flask
from config import Config
from models import db
from routes import register_routes


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Création du dossier d'upload
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    db.init_app(app)
    register_routes(app)

    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    # Creation de l'app
    app = create_app()
    # Lance l’application Flask en mode debug
    app.run(debug=True)
