"""Application principale"""

import os
import click
import logging
import sys
from flask import Flask
from flask_wtf import CSRFProtect
from flask_migrate import Migrate, upgrade
from flask.cli import with_appcontext
from config import Config
from models import db
from routes import register_routes
from backup import export_backup, restore_backup
from maintenance import run_maintenance_hash, convert_to_webp_all

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
MIGRATIONS_DIR = os.path.join(BASE_DIR, "migrations")

csrf = CSRFProtect()


def create_app():
    """
    Initialisation de l'application
    """
    app = Flask(__name__)
    migrate = Migrate()
    app.config.from_object(Config)
    # Logs sur stdout (visibles via `docker logs`)
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        force=True,
    )
    logging.getLogger("prompt_manager").setLevel(app.config["LOG_LEVEL"])
    logging.getLogger("prompt_manager").info(
        "Application démarrée (LOG_LEVEL=%s)", app.config["LOG_LEVEL"])
    csrf.init_app(app)

    if app.config['SECRET_KEY'] == "dev-insecure-change-me":
        print("ATTENTION : SECRET_KEY par défaut utilisée, "
              "à définir en production.")

    # Création du dossier d'upload
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    if not os.path.exists(app.config['DB_FOLDER']):
        os.makedirs(app.config['DB_FOLDER'])

    db.init_app(app)
    migrate.init_app(app, db, directory=MIGRATIONS_DIR)
    register_routes(app)

    if os.path.exists(MIGRATIONS_DIR):
        with app.app_context():
            upgrade()

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

    @app.cli.command("maintenance")
    @with_appcontext
    def maintenance_command():
        """Conversion WebP + calcul des hash manquants."""
        convert_to_webp_all()
        run_maintenance_hash()

    return app


if __name__ == '__main__':
    # Creation de l'app
    appli = create_app()
    # Lance l’application Flask en mode debug
    appli.run(debug=True)
