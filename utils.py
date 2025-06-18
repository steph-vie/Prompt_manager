"""Liste des fonctions utilitaires de l'application"""

from config import ALLOWED_EXTENSIONS


def allowed_file(filename):
    """
    Vérifie si le fichier a une extension autorisée.
    :param filename: Nom du fichier
    :return: Booléen indiquant si le fichier est autorisé
    """
    return ('.' in filename
            and filename.rsplit('.', 1)[1].lower()
            in ALLOWED_EXTENSIONS)


def clean_tags(tag_string):
    """
    Enleve pour chaque tag les expaces avant et apres
    :param filename: Chaine de charactere representant tous les tags
    :return: Chaine de charactere representant tous les tags sans les espaces
    """
    return ','.join(tag.strip().lower() for tag in tag_string.split(','))
