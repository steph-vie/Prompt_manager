# 🎨 Prompt Manager

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.x-yellow.svg)](https://www.python.org/)

Une mini-application Flask pour gérer et explorer des **prompts** (texte + image + tags).  
Pensée pour les amateurs de génération d’images (ComfyUI).

## ✨ Fonctionnalités

### Gestion des prompts
- 📝 **CRUD complet** : Création, lecture, modification et suppression de prompts
- 🖼️ **Galerie visuelle** : Upload et association d'images pour chaque prompt
- 🏷️ **Système de tags avancé** : Organisation par catégories personnalisées avec filtrage intelligent
- 🔍 **Recherche puissante** : Recherche par mots-clés dans les titres et contenus

### Métadonnées automatiques
🔢 **Extraction intelligente** : Récupération automatique depuis les métadonnées d'images
  - Seed
  - Steps
  - Sample
  - Scheduler
  - Checkpoint / Modèle
  - LoRAs utilisés
  - Prompt négatif
  - Un archivage des informations en brut au format json

### Interface moderne
- 🎨 **Design responsive** : Interface élégante avec Bootstrap 5
- 📱 **Mobile-friendly** : Utilisable sur tous les appareils
- ⚡ **Performance optimisée** : Chargement rapide et navigation fluide

## 🛠️ Technologies

### Backend
- **Python 3** - Langage principal
- **Flask** - Framework web minimaliste et puissant
- **SQLAlchemy** - ORM pour la gestion de base de données
- **Flask-Migrate** - Gestion des migrations de schéma

### Base de données
- **SQLite** - Base de données locale légère et performante

### Frontend
- **Bootstrap 5** - Framework CSS moderne  

## 🚀 Installation rapide
### 🖥️ Première installation
#### En local
```bash
git clone https://github.com/steph-vie/Prompt_manager.git
cd Prompt_manager
python3 -m venv venv
source venv/bin/activate   # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
export SECRET_KEY="change-me"  # requis pour sessions/CSRF (mets une vraie clé en prod)
flask run
```
#### En docker
```bash
# 1) Crée ton fichier .env (voir .env.example)
# cp .env.example .env

# 2) Lance le service
docker compose up -d
```

L'application sera accessible à l'adresse : **http://127.0.0.1:5000**

### ⚠️ En cas de maj de l'image
```bash
docker compose up -d --build
```

### 🔧 Configuration `.env`

Le `docker-compose.yml` utilise des variables d’environnement. Un exemple est fourni dans `.env.example`.

- **`SECRET_KEY`**: clé Flask (sessions + CSRF). Génère-en une forte:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

- **`HOST_PORT`**: port exposé sur ta machine (ex: `5000`)
- **`DIR_BASE`**: dossier hôte qui contient le dossier `prompt_manager/` utilisé pour les volumes

## 📜 Licence

MIT — libre d’usage, de partage et de modification.

## 📧 Contact

**Steph Vie** - [@steph-vie](https://github.com/steph-vie)

Lien du projet : [https://github.com/steph-vie/Prompt_manager](https://github.com/steph-vie/Prompt_manager)

---

<div align="center">

**Développé avec ❤️ pour la communauté de l'IA générative**

⭐ **N'oubliez pas de laisser une étoile si ce projet vous aide !** ⭐

</div>