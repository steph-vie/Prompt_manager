"""Liste des fonctions utilitaires de l'application"""

from config import ALLOWED_EXTENSIONS
from models import Category
import json
from PIL import Image


class ComfyUIImage:
    def __init__(self, image_path):
        self.image_path = image_path
        self.prompt = self._extract_prompt()

    def _extract_prompt(self):
        """Extrait le JSON du champ 'prompt' dans les métadonnées PNG"""
        img = Image.open(self.image_path)
        raw = img.info.get("prompt") or img.info.get("parameters")
        if not raw:
            raise ValueError("❌ Aucun champ 'prompt' trouvé dans l'image.")
        try:
            data = json.loads(raw)
            return data
        except json.JSONDecodeError:
            raise ValueError("❌ Impossible de décoder le JSON du champ 'prompt'.")

    def get_value(self, value):
        """Cherche une clé dans tous les nœuds du prompt (inputs seulement)"""
        for key, node in self.prompt.items():
            if value in list(node["inputs"].keys()):
                # value = node.get("inputs", {}).get(key)
                # if value is not None:
                if type(node["inputs"][value]).__name__ != 'list':
                    return node["inputs"][value]

    # Alias pratiques
    def get_positive_prompt(self):
        return self.get_value("positive")

    def get_negative_prompt(self):
        return self.get_value("negative")

    def get_seed(self):
        seed_temp = self.get_value("seed")
        if seed_temp is not None:
            return seed_temp
        else:
            return self.get_value("noise_seed")

    def get_steps(self):
        return self.get_value("steps")

    def get_checkpoint(self):
        return self.get_value("base_ckpt_name").split("/")[-1].replace(".safetensors", "")

    def get_loras(self):
        """Retourne toutes les LoRAs trouvées (liste)"""
        loras = []
        for node in self.prompt.values():
            inputs = node.get("inputs", {})
            for k, v in inputs.items():
                if k.startswith("lora_name_"):
                    loras.append(v.split("/")[-1].replace(".safetensors", ""))

        clean_loras = ",".join(lora.strip() for lora in loras)
        return clean_loras if loras else None


class CategoryService:

    @staticmethod
    def get_tree():
        """Retourne l'arbre des catégories"""
        root_categories = Category.query.filter_by(parent_id=None).all()
        return root_categories

    @staticmethod
    def build_tree_dict(category):
        """Construit un dictionnaire récursif pour l'arbre"""
        return {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'children': [CategoryService.build_tree_dict(child)
                         for child in category.children.all()]
        }

    @staticmethod
    def get_category_options():
        """Retourne les options pour les formulaires (avec indentation)"""
        options = [('', '-- Aucune catégorie --')]

        def add_category_options(categories, level=0):
            for category in categories:
                # Caractère d'espacement japonais pour l'indentation
                indent = "　" * level
                options.append((category.id, f"{indent}{category.name}"))
                add_category_options(category.children.all(), level + 1)

        root_categories = Category.query.filter_by(parent_id=None).all()
        add_category_options(root_categories)

        return options

    @staticmethod
    def move_category(category_id, new_parent_id):
        """Déplace une catégorie (avec vérification de boucles)"""
        category = Category.query.get(category_id)
        new_parent = Category.query.get(new_parent_id) if new_parent_id else None

        # Vérifier qu'on ne crée pas de boucle
        if new_parent and (new_parent.id == category.id or category.is_ancestor_of(new_parent)):
            raise ValueError("Impossible de déplacer : cela créerait une boucle")

        category.parent_id = new_parent_id
        db.session.commit()
        return True


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
