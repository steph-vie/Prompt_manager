"""Fonctions de sauvegarde et de restauration de l'application"""

import json
import os
import shutil
import zipfile
from datetime import datetime, timezone

from flask import current_app

from models import db, Prompt, Category
from version import __version__

SCHEMA_VERSION = "2.0"
JSON_NAME = "backup.json"
IMAGES_PREFIX = "uploads/"


def _iso(value):
    """Date -> texte ISO (ou None)"""
    return value.isoformat() if value else None


def _parse_date(value):
    """Texte ISO -> date (ou None)"""
    return datetime.fromisoformat(value) if value else None


def _build_data():
    """Construit le dictionnaire complet à sauvegarder"""
    categories = Category.query.order_by(Category.id).all()
    prompts = Prompt.query.order_by(Prompt.id).all()

    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "schema_version": SCHEMA_VERSION,
        "application_version": __version__,
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "parent_id": c.parent_id,
                "created_at": _iso(c.created_at),
            }
            for c in categories
        ],
        "prompts": [
            {
                "id": p.id,
                "prompt": p.prompt,
                "tags": p.tags,
                "seed": p.seed,
                "steps": p.steps,
                "checkpoint": p.checkpoint,
                "cfg": p.cfg,
                "loras": p.loras,
                "neg_prompt": p.neg_prompt,
                "sampler": p.sampler,
                "scheduler": p.scheduler,
                "category_id": p.category_id,
                "image_filename": p.image_filename,
                "image_hash": p.image_hash,
                "prompt_raw": p.prompt_raw,
                "created_at": _iso(p.created_at),
                "updated_at": _iso(p.updated_at),
            }
            for p in prompts
        ],
    }


def export_backup(filepath="backup.json"):
    """
    Exporte la base.
    Extension .json : base seule. Extension .zip : base + images.
    """
    data = _build_data()
    payload = json.dumps(data, indent=4, ensure_ascii=False)

    if filepath.lower().endswith(".zip"):
        upload_dir = current_app.config['UPLOAD_FOLDER']
        with zipfile.ZipFile(filepath, "w") as archive:
            archive.writestr(JSON_NAME, payload,
                             compress_type=zipfile.ZIP_DEFLATED)
            for prompt in data["prompts"]:
                name = prompt["image_filename"]
                if not name:
                    continue
                path = os.path.join(upload_dir, name)
                if os.path.isfile(path):
                    # Les WebP sont déjà compressés : stockage direct
                    archive.write(path, IMAGES_PREFIX + name,
                                  compress_type=zipfile.ZIP_STORED)
    else:
        with open(filepath, "w", encoding="utf-8") as file:
            file.write(payload)


def _restore_database(data):
    """Remplace le contenu de la base, dans une seule transaction."""
    if (not isinstance(data, dict)
            or "categories" not in data or "prompts" not in data):
        raise ValueError("Fichier de sauvegarde invalide.")

    try:
        Prompt.query.delete()
        Category.query.delete()

        # Catégories créées sans parent, puis rattachées : l'ordre des ids
        # ne garantit pas que le parent existe avant l'enfant.
        parents = {}
        for cat in data["categories"]:
            db.session.add(Category(
                id=cat["id"],
                name=cat["name"],
                description=cat.get("description"),
                created_at=_parse_date(cat.get("created_at")),
            ))
            if cat.get("parent_id") is not None:
                parents[cat["id"]] = cat["parent_id"]
        db.session.flush()

        for cat_id, parent_id in parents.items():
            Category.query.filter_by(id=cat_id).update(
                {"parent_id": parent_id})

        for item in data["prompts"]:
            seed = item.get("seed")
            db.session.add(Prompt(
                id=item["id"],
                prompt=item["prompt"],
                tags=item.get("tags"),
                seed=None if seed is None else str(seed),
                steps=item.get("steps"),
                checkpoint=item.get("checkpoint"),
                cfg=item.get("cfg"),
                loras=item.get("loras"),
                neg_prompt=item.get("neg_prompt"),
                sampler=item.get("sampler"),
                scheduler=item.get("scheduler"),
                category_id=item.get("category_id"),
                image_filename=item.get("image_filename"),
                image_hash=item.get("image_hash"),
                prompt_raw=item.get("prompt_raw"),
                created_at=_parse_date(item.get("created_at")),
                updated_at=_parse_date(item.get("updated_at")),
            ))

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def _restore_images(archive):
    """Copie les images de l'archive dans le dossier d'upload."""
    upload_dir = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)

    for member in archive.namelist():
        if not member.startswith(IMAGES_PREFIX) or member.endswith("/"):
            continue
        name = member[len(IMAGES_PREFIX):]
        # Refuse les sous-dossiers et les chemins du type "../"
        if not name or name != os.path.basename(name):
            continue
        with archive.open(member) as source, \
                open(os.path.join(upload_dir, name), "wb") as target:
            shutil.copyfileobj(source, target)


def restore_backup(filepath="backup.json"):
    """
    Restaure la base depuis un .json (base seule) ou un .zip (base + images).
    """
    if filepath.lower().endswith(".zip"):
        with zipfile.ZipFile(filepath) as archive:
            if JSON_NAME not in archive.namelist():
                raise ValueError(f"{JSON_NAME} absent de l'archive.")
            data = json.loads(archive.read(JSON_NAME).decode("utf-8"))
            _restore_database(data)
            _restore_images(archive)
    else:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
        _restore_database(data)
