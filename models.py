"""Definition des modeles presents dans l'application"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Prompt(db.Model):  # pylint: disable=too-few-public-methods
    """
    Modèle représentant un prompt dans la base de données.
    Contient un titre, le texte du prompt, des tags, un fichier image associé
    et une date de création.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(120), nullable=True)
    image_filename = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prompt {self.title}>'
