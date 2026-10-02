"""Liste des fonctions procedant à la maintenance generale de l'application"""

import os
from pathlib import Path
from flask import current_app
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import defer
from models import Prompt, db
from utils import convert_to_webp, create_thumbnail, get_file_hash


def _upload_path(filename):
    """Chemin absolu d'un fichier du dossier d'upload"""
    return os.path.join(current_app.config['UPLOAD_FOLDER'], filename)


def convert_to_webp_all():
    """
    Convertit en WebP les images qui ne le sont pas encore,
    met à jour la BDD puis supprime l'ancien fichier.
    """
    print("**** Maintenance WebP ****")
    prompts = (
        Prompt.query
        .filter(Prompt.image_filename.isnot(None),
                ~Prompt.image_filename.like('%.webp'))
        .options(defer(Prompt.prompt_raw))
        .all()
    )

    converted = 0

    for prompt in prompts:

        source = _upload_path(prompt.image_filename)
        if not os.path.exists(source):
            print(f"Fichier introuvable, ignoré : {prompt.image_filename}")
            continue
        try:
            convert_to_webp(source)
        except OSError as err:
            print(f"Échec de conversion de {prompt.image_filename} : {err}")
            continue

        prompt.image_filename = str(
            Path(prompt.image_filename).with_suffix(".webp"))
        prompt.image_hash = None  # sera recalculé sur le fichier WebP
        db.session.commit()
        os.remove(source)
        converted += 1

    print(f"{converted} image(s) converties" if converted
          else "Toutes les images sont en WebP")


def run_maintenance_hash():
    """Calcule et stocke le hash des images qui n'en ont pas."""
    print("**** Maintenance hash ****")
    prompts = (
        Prompt.query
        .filter(Prompt.image_filename.isnot(None),
                Prompt.image_hash.is_(None))
        .options(defer(Prompt.prompt_raw))
        .all()
    )

    done = 0
    for prompt in prompts:
        path = _upload_path(prompt.image_filename)
        if not os.path.exists(path):
            print(f"Fichier introuvable, ignoré : {prompt.image_filename}")
            continue

        prompt.image_hash = get_file_hash(path)
        try:
            db.session.commit()
            done += 1
        except IntegrityError:
            db.session.rollback()
            print(f"Doublon détecté pour le prompt {prompt.id}, "
                  "hash non enregistré")

    total = Prompt.query.filter(Prompt.image_hash.isnot(None)).count()
    print(f"{done} hash calculés, {total} hash dans la base")

def create_missing_thumbs():
    """Crée les miniatures manquantes (images existantes, restauration...)."""
    print("**** Maintenance miniatures ****")
    thumbs_dir = current_app.config['THUMBS_FOLDER']
    os.makedirs(thumbs_dir, exist_ok=True)

    filenames = [
        name for (name,) in db.session.query(Prompt.image_filename)
        .filter(Prompt.image_filename.isnot(None))
    ]

    created = 0
    for name in filenames:
        thumb_path = os.path.join(thumbs_dir, name)
        source = _upload_path(name)
        if os.path.exists(thumb_path) or not os.path.exists(source):
            continue
        try:
            create_thumbnail(source, thumb_path)
            created += 1
        except OSError as err:
            print(f"Échec de la miniature pour {name} : {err}")

    print(f"{created} miniature(s) créée(s)")