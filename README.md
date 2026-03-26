# Prompt Manager 💫

Une mini-application Flask pour gérer et explorer des **prompts** (texte + image + tags).  
Pensée pour les amateurs de génération d’images (Stable Diffusion, ComfyUI, etc.).

## ✨ Fonctionnalités
- CRUD complet des prompts (ajout, édition, suppression)  
- Téléversement d’images associées  
- Extraction de métadonnées (seed, steps, Lora, prompt négatif…)  
- Tags, recherche et filtrage par mots-clés et catégories
- Interface responsive avec Bootstrap 5  

## 🛠️ Stack
- Python 3 + Flask  
- SQLite + SQLAlchemy  
- Bootstrap 5  

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

### ⚠️ En cas de MAJ
il faut upgrader la base
```bash
flask db upgrade
```
🌐 → http://127.0.0.1:5000

## 🐳 Docker

Le dépôt inclut Dockerfile et docker-compose.yml pour un déploiement simplifié.

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
