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
    __tablename__ = "prompts"

    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(120), nullable=True)

    # Métadonnées techniques
    seed = db.Column(db.Integer, nullable=True)
    steps = db.Column(db.Integer, nullable=True)
    checkpoint = db.Column(db.Text, nullable=True)
    cfg = db.Column(db.Float, nullable=True)
    loras = db.Column(db.Text, nullable=True)
    neg_prompt = db.Column(db.Text, nullable=True)
    prompt_raw = db.Column(db.JSON, nullable=True)
    sampler = db.Column(db.String(120), nullable=True)
    scheduler = db.Column(db.String(120), nullable=True)

    # Ajout de la référence à la catégorie
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", name="fk_prompt_category"),
        nullable=True
    )

    # Image et timestamps
    image_filename = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Prompt {self.id}>"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Foreign key récursive avec un nom explicite
    parent_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", name="fk_category_parent"),
        nullable=True
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relation récursive explicite
    children = db.relationship(
        "Category",
        backref=db.backref("parent", remote_side=[id]),
        lazy="dynamic",
        foreign_keys=[parent_id]  # 🔑 on précise quelle FK utiliser
    )

    # Relation avec les prompts
    prompts = db.relationship("Prompt", backref="category", lazy="dynamic")

    def __repr__(self):
        return f"<Category {self.name}>"

    def get_path(self):
        """Retourne le chemin complet de la catégorie (breadcrumbs)"""
        path = [self.name]
        current = self.parent
        while current:
            path.append(current.name)
            current = current.parent
        return " > ".join(reversed(path))

    def get_all_children(self):
        """Récupère récursivement tous les enfants"""
        children = []
        for child in self.children:
            children.append(child)
            children.extend(child.get_all_children())
        return children

    def is_ancestor_of(self, category):
        """Vérifie si cette catégorie est ancêtre d'une autre"""
        current = category.parent
        while current:
            if current.id == self.id:
                return True
            current = current.parent
        return False
