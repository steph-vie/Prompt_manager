"""applique diverses maintenances au démarrage de l'application"""


import os
from models import Prompt, db
from pathlib import Path
from flask import current_app
from utils import convert_to_webp


def convert_to_webp_all():
    """Convertion de toutes les images png avec remplacement
    de l'extension dans la BDD
    """
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
        print("tous les prompts ont des images en Webp")
    else:
        print(f"Modification de {nbr_convert_to_webp} prompts")


def run_maintenance_hash():
    """
    créé et stocke dans la bdd les hash pour images webp qui n'en ont pas
    """
    print("maintenance hash")
