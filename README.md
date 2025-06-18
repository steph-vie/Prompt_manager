![Pylint 3.9](https://github.com/steph_vie/Prompt_manager/raw/main/badges/pylint-3.9.svg)
![Pylint 3.10](https://github.com/steph_vie/Prompt_manager/raw/main/badges/pylint-3.10.svg)
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

## 🚀 Installation locale

1. **Clone du dépôt** :
   ```bash
   git clone https://github.com/votre-utilisateur/prompt-library.git
   cd prompt-library
   
2. **Création d’un environnement virtuel** :
    ```bash
   python3 -m venv venv
   source venv/bin/activate

3. **Installation des dépendances** :
   ```bash
   pip install flask flask_sqlalchemy

4. **Lancement de l’application** :
   ```bash
   flask run
   
L'application sera accessible à l'adresse : http://127.0.0.1:5000

## 📦 Utilisation avec Docker
Crée un fichier Dockerfile :

      FROM python:3.11-slim

      WORKDIR /app
      COPY . /app

      RUN pip install flask flask_sqlalchemy
      ENV FLASK_APP=app.py

      CMD ["flask", "run", "--host=0.0.0.0"]

Crée un docker-compose.yml :

      version: '3'
      services:
         app:
            build: .
          ports:
            - \"5000:5000\"
          volumes:
            - ./static/uploads:/app/static/uploads
            - ./prompts.db:/app/prompts.db

Lancer avec Docker :
      ```bash
      docker-compose up --build


## 📁 Structure du projet

      prompt-library/
      ├── app.py
      ├── prompts.db
      ├── static/
      │   └── uploads/
      ├── templates/
      │   ├── base.html
      │   ├── index.html
      │   ├── add.html
      │   ├── edit.html
      │   └── view.html
      └── README.md

## 📝 Licence
Ce projet est open source et distribué sous licence MIT.
