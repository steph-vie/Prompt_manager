"""Application principale"""

import os
from flask import Flask
from flask_migrate import Migrate, upgrade
from config import Config
from models import db
from routes import register_routes
import click
from flask.cli import with_appcontext
from backup import export_backup, restore_backup


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

    @app.cli.command("backup")
    @click.option("--output", default="backup.json", help="Fichier de sortie")
    @with_appcontext
    def backup_command(output):
        """Export complet de la base en JSON."""
        export_backup(output)
        click.echo(f"Backup créé : {output}")

    @app.cli.command("restore")
    @click.option("--input", default="backup.json", help="Fichier à restaurer")
    @with_appcontext
    def restore_command(input):
        """Restauration complète depuis un JSON."""
        restore_backup(input)
        click.echo(f"Base restaurée depuis : {input}")

    return app


if __name__ == '__main__':
    # Creation de l'app
    appli = create_app()
    # Lance l’application Flask en mode debug
    appli.run(debug=True)
