"""Initialisation du module"""

from .prompt_routes import prompt_bp


def register_routes(app):
    """
    Enregistrement des routes
    """
    app.register_blueprint(prompt_bp)
