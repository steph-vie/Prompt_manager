"""Liste des fonctions utilitaires de l'application"""

import json
from pathlib import Path
from PIL import Image
from config import ALLOWED_EXTENSIONS
from models import db, Category


class ComfyUIImage:
    """Fonction globale représentant l'image uploadée"""

    def __init__(self, image_path):
        self.image_path = image_path
        self.prompt = self._extract_prompt()
        self.workflow_type = self._detect_workflow()

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
            raise ValueError(
                "❌ Impossible de décoder le JSON du champ 'prompt'."
            )

    def _detect_workflow(self):
        """Détecte le type de workflow utilisé."""

        class_types = {
            node.get("class_type")
            for node in self.prompt.values()
        }

        if "UNETLoader" in class_types:
            return "anima"
        return "illustrious"

    @property
    def is_illustrious(self):
        """teste si le type du workflow est illustrious"""

        return self.workflow_type == "illustrious"

    @property
    def is_anima(self):
        """teste si le type du workflow est anima"""

        return self.workflow_type == "anima"

    #
    # Helpers
    #
    def find_node(self, class_type):
        """Retourne le noeud pour la class_type donnée"""

        for node in self.prompt.values():
            if node.get("class_type") == class_type:
                return node
        return None

    def find_nodes(self, class_type):
        """Retourne les noeuds pour la class_type donnée"""
        return [
            node
            for node in self.prompt.values()
            if node.get("class_type") == class_type
        ]

    def find_node_by_title(self,title):
        """Retourne le noeud pour un titre donné"""
        for node in self.prompt.values():
            node_title = node.get("_meta", {}).get("title", "")
            if str(node_title).lower() == title:
                return node
        return None


    def get_input(self, node, key, default=None):
        """Retourne la valeur dans imputs pour la clée donnée"""
        if not node:
            return default
        return node.get("inputs", {}).get(key, default)

    def get_value(self, value):
        """Cherche une clé dans tous les nœuds du prompt (inputs seulement)"""

        for key, node in self.prompt.items():
            if value in list(node["inputs"].keys()):
                inputs = node.get("inputs", {})

                if value in inputs and not isinstance(inputs[value], list):
                    return inputs[value]

        return None

    #
    # KSampler
    #
    def get_sampler_node(self):
        """Retourne le noeud du sampler"""
        return (
                self.find_node("KSampler")
                or self.find_node("KSampler SDXL (Eff.)")
        )

    #
    # Prompts
    #
    def get_positive_prompt(self):
        """Retourne le prompt positif"""

        # Workflow Illustrious
        prompt = self.get_value("positive")
        if isinstance(prompt, str):
            return prompt

        # Workflow Anima

        # Dans le cas d'un noeud CLIPTextEncode
        for node in self.find_nodes("CLIPTextEncode"):
            title = node.get("_meta", {}).get("title", "")
            if "positive" in str(title).lower():
                prompt = self.get_input(node, "text")
                if isinstance(prompt, str):
                    return prompt

        # Dans le cas d'un noeud ImpactWildcardProcessor
        for node in self.find_nodes("ImpactWildcardProcessor"):
            title = node.get("_meta", {}).get("title", "")
            if "positive" in str(title).lower():
                prompt = self.get_input(node, "populated_text")
                if isinstance(prompt, str):
                    return prompt

        return "Prompt non trouvé"

    def get_negative_prompt(self):
        """Retourne le prompt négatif"""

        # Workflow Illustrious
        prompt = self.get_value("negative")
        if isinstance(prompt, str):
            return prompt

        # Workflow Anima
        for node in self.find_nodes("CLIPTextEncode"):
            title = node.get("_meta", {}).get("title", "")
            if "Negative" in title:
                prompt = self.get_input(node, "text")
                if isinstance(prompt, str):
                    return prompt
                else:
                    return "Prompt non trouvé"

        return None

    def get_seed(self):
        """Retourne le seed"""

        seed_temp = self.get_value("seed")
        if seed_temp is not None:
            return seed_temp
        return self.get_value("noise_seed")

    def get_cliploader(self):
        """Retourne le clip Loader"""

        node = self.find_node("CLIPLoader")
        if node:
            cliploader = self.get_input(node, "clip_name")
            return cliploader

        return None

    def get_steps(self):
        """Retourne les Steps"""

        steps = self.get_value("steps")
        if steps is not None:
            return steps

        node = self.find_node_by_title("steps")
        if node is not None:
            steps = self.get_input(node,"value")
            return steps

        return None

    def get_cfg(self):
        """Retourne le CFG"""

        cfg = self.get_value("cfg")
        if cfg is not None:
            return cfg

        node = self.find_node_by_title("cfg")
        if node is not None:
            cfg = self.get_input(node, "value")
            return cfg

    def get_sampler(self):
        """Retourne le sampler"""

        return self.get_value("sampler_name")


    def get_scheduler(self):
        """Retourne le scheduler"""

        return self.get_value("scheduler")

    #
    # Checkpoint
    #
    def get_checkpoint(self):
        """Retourne le Checkpoint"""

        # Illustrious
        node = self.find_node("Eff. Loader SDXL")
        if node:
            checkpoint = self.get_input(node, "base_ckpt_name")
            if checkpoint:
                return checkpoint.split("/")[-1].replace(".safetensors", "")

        # Anima
        node = self.find_node("UNETLoader")
        if node:
            checkpoint = self.get_input(node, "unet_name")
            if checkpoint:
                return checkpoint.split("/")[-1].replace(".safetensors", "")

        return None

    #
    # LoRAs
    #
    def get_loras(self):
        """Retourne les Loras"""
        loras = {}

        # Format CR LoRA Stack (Illustrious)
        for node in self.prompt.values():
            inputs = node.get("inputs", {})

            for key, value in inputs.items():

                if not key.startswith("lora_name"):
                    continue

                index = key.split("_")[-1]

                if not value or value == "None":
                    continue

                name = value.split("/")[-1].replace(".safetensors", "")
                weight = inputs.get(f"model_weight_{index}")
                if weight is not None:
                    loras[name] = weight
                else:
                    weight = inputs.get("strength_model")
                    loras[name] = weight

        # Format LoraLoaderModelOnly (Anima)
        for node in self.find_nodes("LoraLoaderModelOnly"):

            name = self.get_input(node, "lora_name")

            if not name:
                continue

            name = name.split("/")[-1].replace(".safetensors", "")

            loras[name] = self.get_input(
                node,
                "strength_model",
                1.0
            )

        return loras or None

    def get_prompt_raw(self):
        """Retourne le prompt brut"""
        return self.prompt

    def optimize_image(self, output_path, quality=90):
        """Convertit l'image en WebP optimisé."""

        with Image.open(self.image_path) as image:
            image.save(
                output_path,
                "WEBP",
                quality=quality,
                method=6
            )


class CategoryService:
    """Gestion des catégories"""

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
            """Ajoute les options"""
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
        new_parent = (
            Category.query.get(new_parent_id)
            if new_parent_id
            else None
        )

        # Vérifier qu'on ne crée pas de boucle
        if new_parent and (new_parent.id == category.id
                           or category.is_ancestor_of(new_parent)):
            raise ValueError(
                "Impossible de déplacer : cela créerait une boucle"
            )

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
    Enlève pour chaque tag les espaces avant et apres
    :param tag_string: Chaine de caractère représentant tous les tags
    :return: Chaine de caractère représentant tous les tags sans les espaces
    """
    return ','.join(tag.strip().lower() for tag in tag_string.split(','))


def taille_path(path, lisible=True):
    """Retourne la taille du chemin donné"""
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"{path} n'existe pas")

    # Calcul taille
    if path.is_file():
        taille = path.stat().st_size
    else:
        taille = sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

    if not lisible:
        return taille

    # Format lisible
    for unite in ['o', 'Ko', 'Mo', 'Go', 'To', 'Po']:
        if taille < 1024:
            return f"{taille:.2f} {unite}"
        taille /= 1024

    return f"{taille:.2f} Po"


def convert_to_webp(path_image):
    """Convertit l'image passée en parametre au format webp"""

    filename_webp = str(Path(path_image).with_suffix(".webp"))
    with Image.open(path_image) as image:
        image.save(
            filename_webp,
            "WEBP",
            quality=90,
            method=6
        )
