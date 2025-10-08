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
### 🖥️ 1er installation
#### En local
```bash
git clone https://github.com/steph-vie/Prompt_manager.git
cd Prompt_manager
python3 -m venv venv
source venv/bin/activate   # ou venv\Scripts\activate sous Windows
pip install -r requirements.txt
flask run
```
#### En docker
```bash
docker compose run -d
```

### ⚠️ En cas de MAJ
il faut upgrader la base
```bash
flask db upgrade
```
🌐 → http://127.0.0.1:5000

## 🐳 Docker

Le dépôt inclut Dockerfile et docker-compose.yml pour un déploiement simplifié.

## 📜 Licence

MIT — libre d’usage, de partage et de modification.
