# 🎨 Prompt Manager

[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.x-yellow.svg)](https://www.python.org/)

Une mini-application Flask pour gérer et explorer des **prompts** (texte + image + tags).  
Pensée pour les amateurs de génération d’images (ComfyUI).

## ✨ Fonctionnalités

### Gestion des prompts
- 📝 **CRUD complet** : Création, lecture, modification et suppression de prompts (avec identification de doublons)
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
cp .env.example .env

# 2) Lance le service
docker compose up -d
```

L'application sera accessible à l'adresse : **http://127.0.0.1:5000**

### ⚠️ En cas de maj de l'image
récuperer les Maj
```bash
docker compose up -d --build
```

### 🔧 Configuration `.env`

Le `docker-compose.yml` utilise des variables d’environnement. Un exemple est fourni dans `.env.example`.

- **`SECRET_KEY`**: clé Flask (sessions + CSRF). Génère-en une forte:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

- **`HOST_PORT`**: Port exposé sur ta machine (ex: `5000`)
- **`DIR_BASE`**: Chemin absolue du dossier `Prompt_manager/` (utilisé pour les volumes)
- **`VERSION`**: Possibilité d'avoir plusieurs instances de l'app, donc plusieurs images (latest par défaut)
- **`LOG_LEVEL`**: Paramtre le niveau de log

## 🔨 Utilitaires

Ces commandes passent par la CLI Flask. Avec Docker, préfixe-les par `docker compose exec app` ; en local, utilise `flask ...` (ou `python.exe -m flask ...` sous Windows). `--help` donne le détail de chaque commande.

### 💾 Sauvegarde

Extraction de la base, avec ou sans les images :

```bash
# Docker : écris dans /app/database (volume) pour retrouver le fichier
# sur ta machine, dans ${DIR_BASE}/database/
docker compose exec app flask backup --output /app/database/backup.zip

# En local
python.exe -m flask backup --output backup.zip
```

- `.zip` : la base (`backup.json`) **et** les images (`uploads/`)
- `.json` : la base seule (`backup.json` par défaut)
- Les miniatures ne sont pas sauvegardées : elles sont régénérées par la maintenance

### ♻️ Restauration

```bash
# Docker
docker compose exec app flask restore --input /app/database/backup.zip

# En local
python.exe -m flask restore --input backup.zip
```

- Accepte un `.zip` (base + images) ou un `.json` (base seule)
- **Remplace tout le contenu de la base** (prompts et catégories)
- Atomique : en cas d'erreur, la base reste inchangée
- Les anciens `backup.json` restent compatibles

Après la restauration d'un ancien `backup.json` (sans hash d'image) ou d'un `.zip`, lance la maintenance pour recalculer les hash et régénérer les miniatures.

### 🧹 Maintenance

```bash
# Docker
docker compose exec app flask maintenance

# En local
python.exe -m flask maintenance
```

Elle :
1. convertit au format WebP les images qui ne le sont pas encore (l'ancien fichier est supprimé) ;
2. calcule le hash des images qui n'en ont pas (détection des doublons) ;
3. crée les miniatures manquantes dans `static/uploads/thumbs/`.

Elle peut être relancée sans risque à tout moment. Les fichiers introuvables et les doublons sont signalés dans les logs, sans bloquer l'exécution.

- **Docker** : elle est lancée automatiquement à chaque démarrage du conteneur.
- **En local** : `flask run` ne la lance pas, pense à l'exécuter après une mise à jour.

### 🩺 Suivi du service

Le conteneur dispose d'un `HEALTHCHECK` qui interroge la route `/health` (accès à la base compris). Après un démarrage, compte environ une minute : la maintenance s'exécute avant le serveur, et peut durer plus longtemps sur une grosse bibliothèque.


```

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