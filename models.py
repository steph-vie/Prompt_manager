"""Definition des modeles presents dans l'application"""

from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def utcnow():
    """Date/heure UTC sans fuseau (compatible avec les données existantes)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Prompt(db.Model):  # pylint: disable=too-few-public-methods
    """
    Modèle représentant un prompt : prompt positif et négatif, paramètres de génération
    (seed, steps, cfg, sampler, scheduler, checkpoint, LoRAs),
    tags, catégorie, image associée et son hash.
    """
    __tablename__ = "prompts"

    id = db.Column(db.Integer, primary_key=True)
    prompt = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(120), nullable=True)

    # Métadonnées techniques
    seed = db.Column(db.String(32), nullable=True)
    steps = db.Column(db.Integer, nullable=True)
    checkpoint = db.Column(db.Text, nullable=True)
    cfg = db.Column(db.Float, nullable=True)
    loras = db.Column(db.JSON, nullable=True)
    neg_prompt = db.Column(db.Text, nullable=True)
    prompt_raw = db.Column(db.JSON, nullable=True)
    sampler = db.Column(db.String(120), nullable=True)
    scheduler = db.Column(db.String(120), nullable=True)
    image_hash = db.Column(db.String(64), unique=True,
                           index=True, nullable=True)

    # Ajout de la référence à la catégorie
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.id", name="fk_prompt_category"),
        nullable=True
    )

    # Image et timestamps
    image_filename = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime,
                           default=utcnow,
                           onupdate = utcnow)

    def __repr__(self):
        return f"<Prompt {self.id}>"


class Category(db.Model):
    """Modèle représentant une catégorie (arborescente) de prompts"""
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

    created_at = db.Column(db.DateTime, default=utcnow)

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
