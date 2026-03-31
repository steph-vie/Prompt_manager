import json
from datetime import datetime
from models import db, Prompt, Category
from version import __version__


def export_backup(filepath="backup.json"):
    categories = Category.query.all()
    prompts = Prompt.query.all()

    data = {
        "exported_at": datetime.utcnow().isoformat(),
        "schema_version": "1.0",
        "application_version": __version__,
        "categories": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "parent_id": c.parent_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
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
                "loras": p.loras,
                "neg_prompt": p.neg_prompt,
                "category_id": p.category_id,
                "image_filename": p.image_filename,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            }
            for p in prompts
        ],
    }

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def restore_backup(filepath="backup.json"):
    from datetime import datetime

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    Prompt.query.delete()
    Category.query.delete()
    db.session.commit()

    for c in data["categories"]:
        category = Category(
            id=c["id"],
            name=c["name"],
            description=c["description"],
            parent_id=c["parent_id"],
            created_at=datetime.fromisoformat(c["created_at"]) if c["created_at"] else None,
        )
        db.session.add(category)

    db.session.commit()

    for p in data["prompts"]:
        prompt = Prompt(
            id=p["id"],
            prompt=p["prompt"],
            tags=p["tags"],
            seed=p["seed"],
            steps=p["steps"],
            checkpoint=p["checkpoint"],
            loras=p["loras"],
            neg_prompt=p["neg_prompt"],
            category_id=p["category_id"],
            image_filename=p["image_filename"],
            created_at=datetime.fromisoformat(p["created_at"]) if p["created_at"] else None,
            updated_at=datetime.fromisoformat(p["updated_at"]) if p["updated_at"] else None,
        )
        db.session.add(prompt)

    db.session.commit()
