''' Definition de la configuration générale de l'application'''
import os


# Definition des repertoires de travail
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
DB_FOLDER = os.path.join(BASE_DIR, 'database')

# Extensions de fichiers autorisées pour les images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


class Config:  # pylint: disable=too-few-public-methods
    """
    Definition des valeurs
    """
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(DB_FOLDER,
                                                          'prompts.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = UPLOAD_FOLDER
    DB_FOLDER = DB_FOLDER
    IMG_PER_PAGE = int(os.environ.get("IMG_PER_PAGE", 24))
