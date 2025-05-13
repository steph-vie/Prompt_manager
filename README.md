# 📸 Prompt Library – Gestionnaire de Prompts pour la Génération d'Images

Une mini application Flask pour organiser vos prompts de génération d'images (ex. : ComfyUI, Stable Diffusion). Chaque prompt peut être tagué, accompagné d'une image d'exemple et recherché par mots-clés.

## ✨ Fonctionnalités

- Ajout, édition, suppression de prompts
- Téléversement d'une image associée à chaque prompt
- Système de tags (filtrage inclus)
- Recherche par mots-clés (titre ou contenu du prompt)
- Interface responsive avec Bootstrap 5

## 🧱 Technologies

- Python 3
- Flask
- SQLite (base de données locale)
- SQLAlchemy
- Bootstrap (CDN)

1. **Clone du dépôt** :
   ```bash
   git clone https://github.com/votre-utilisateur/prompt-library.git
   cd prompt-library

2. **Création d’un environnement virtuel** :
 ```bash
  python3 -m venv venv
  source venv/bin/activate
