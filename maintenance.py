"""Liste des fonctions procedant à la maintenance generale de l'application"""

import os
from pathlib import Path
from flask import current_app
from models import Prompt, db
from utils import convert_to_webp,get_file_hash


def convert_to_webp_all():
    """
    Convertion de toutes les images png avec remplacement
    de l'extension dans la BDD
    """
    print("**** Maintenance WebP ****")
    all_prompts = Prompt.query.all()
    nbr_convert_to_webp = 0
    for prompt in all_prompts:

        ext = os.path.splitext(prompt.image_filename)[1]
        if ext != ".webp":

            path_image_filename_ab = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                prompt.image_filename)
            print(f"Modification de :{prompt.image_filename}")

            # Convertion en WEBP
            convert_to_webp(path_image_filename_ab)
            nbr_convert_to_webp = nbr_convert_to_webp + 1

            # Enregistrement du nouveau nom
            new_image_filename = str(Path(
                                    prompt.image_filename)
                                    .with_suffix(".webp"))
            prompt.image_filename = new_image_filename
            db.session.commit()
    if nbr_convert_to_webp == 0:
        print("Tous les prompts ont des images en Webp")
    else:
        print(f"Modification de {nbr_convert_to_webp} prompts")


def run_maintenance_hash():
    """
    créé et stocke dans la bdd les hash pour images webp qui n'en ont pas
    """
    print("**** Maintenance hash ****")
    nbr_hash = 0
    nbr_no_hash = 0
    all_prompts = Prompt.query.all()
    for prompt in all_prompts:
        if prompt.image_hash:
            nbr_hash = nbr_hash + 1
        else:
            nbr_no_hash = nbr_no_hash + 1
            path_image_filename_ab = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                prompt.image_filename)
            print(f"Obtention du hash pour {prompt.id}")

            # Obtention du hash
            new_hash = get_file_hash(path_image_filename_ab)
            print(f"Nouveau hash: {new_hash}")

            # Sauvegarde du hash dans la bdd
            prompt.image_hash = new_hash
            db.session.commit()

    if nbr_no_hash == 0:
        print(f"Tous les prompts ont un hash")
    else:
        print(f"{nbr_no_hash} hash obtenus")

    print(f"{nbr_hash} hash dans la base")
