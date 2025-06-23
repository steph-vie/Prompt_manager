# ✏️ Prompt Manager – Gestionnaire de Prompts pour la Génération d'Images

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

## 🚀 Installation locale

1. **Clone du dépôt** :
   ```bash
   git clone https://github.com/steph-vie/Prompt_manager.git
   cd Prompt_manager
   
2. **Création d’un environnement virtuel** :
    ```bash
   python3 -m venv venv
   source venv/bin/activate

3. **Installation des dépendances** :
   ```bash
   pip install -r requirement.txt
   
4. **Lancement de l’application** :
   ```bash
   python app.py
   
L'application sera accessible à l'adresse : http://127.0.0.1:5000

## 📦 Utilisation avec Docker
Modifier les fichiers `docker-compose.yml` et `.env` en conséquence

## 📝 Licence
Ce projet est open source et distribué sous licence MIT.

