"""Liste de toutes les routes de l'application"""

import os
import uuid
from collections import Counter
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, jsonify
)
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import defer
from config import IMPORT_EXTENSIONS
from models import db, Prompt, Category
from utils import (
    ComfyUIImage, allowed_file, clean_tags, CategoryService,
    taille_path, get_file_hash, save_webp)
from version import __version__

prompt_bp = Blueprint('prompt', __name__)


def get_sidebar_data():
    """Données communes du panneau Filtres (catégories + tags)."""
    category_prompt_counts = dict(
        db.session.query(Prompt.category_id, func.count(Prompt.id))
        .filter(Prompt.category_id.isnot(None))
        .group_by(Prompt.category_id)
        .all()
    )
    category_children_counts = dict(
        db.session.query(Category.parent_id, func.count(Category.id))
        .filter(Category.parent_id.isnot(None))
        .group_by(Category.parent_id)
        .all()
    )
    # On ne charge que la colonne tags, pas les objets complets
    all_tags = {
        tag.strip().lower()
        for (tags,) in db.session.query(Prompt.tags)
        for tag in (tags or '').split(',')
        if tag.strip()
    }
    return {
        "category_prompt_counts": category_prompt_counts,
        "category_children_counts": category_children_counts,
        "tags": sorted(all_tags),
    }


@prompt_bp.app_context_processor
def inject_sidebar():
    """Rend disponibles dans tous les templates les variables de base.html."""
    return {
        "app_version": __version__,
        "category_tree": CategoryService.get_tree(),
        **get_sidebar_data(),
    }


@prompt_bp.route('/')
@prompt_bp.route('/category/<int:category_id>')
def index(category_id=None):

    """
    Route principale affichant la liste des prompts.
    Prend en compte les filtres par tag ou par requête de recherche.
    """
    selected_category = None
    if category_id:
        selected_category = Category.query.get_or_404(category_id)

    tag = request.args.get('tag')
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)

    prompts_query = Prompt.query

    # Filtrer par catégorie si sélectionnée
    if selected_category:
        # Récupérer les IDs de la catégorie et de ses enfants
        category_ids = [selected_category.id]
        category_ids.extend([child.id for child in selected_category.
                             get_all_children()])
        prompts_query = (prompts_query.filter(
            Prompt.category_id.
            in_(category_ids)))

    if tag:
        prompts_query = prompts_query.filter(Prompt.tags.like(f'%{tag}%'))
    if query:
        prompts_query = prompts_query.filter(
            (Prompt.prompt.contains(query))
            | (Prompt.checkpoint.contains(query))
            | (Prompt.loras.contains(query))
            | (Prompt.neg_prompt.contains(query))
        )

    # prompt_raw (workflow complet) est inutile sur la grille
    pagination = (
        prompts_query
        .options(defer(Prompt.prompt_raw))
        .order_by(Prompt.id.desc())
        .paginate(page=page, per_page=current_app.config['IMG_PER_PAGE'])
    )

    return render_template('index.html',
                           prompts=pagination.items,
                           selected_tag=tag,
                           query=query or '',
                           pagination=pagination,
                           selected_category=selected_category)


@prompt_bp.route('/prompt/<int:prompt_id>')
def view(prompt_id):

    """
    Affiche les détails d’un prompt spécifique.
    :param prompt_id: ID du prompt à afficher
    """

    prompt = db.get_or_404(Prompt, prompt_id)
    return render_template('view.html', prompt=prompt)


@prompt_bp.route('/add', methods=['GET', 'POST'])
def add():

    """
    Ajoute un nouveau prompt à partir d'une image ComfyUI (PNG)
    """
    category_options = CategoryService.get_category_options()

    if request.method == 'POST':
        tags_cleaned = clean_tags(request.form.get('tags', ''))
        categorie_id = request.form.get('categorie', type=int)
        image = request.files.get('image')
        filename = None

        # L'extraction de métadonnées repose sur l'image source.
        if (not image or not image.filename
                or not allowed_file(image.filename, IMPORT_EXTENSIONS)):
            flash("Une image PNG générée par ComfyUI est obligatoire "
                  "pour créer un prompt.", "error")
            return redirect(url_for('.add'))

        # Lecture des métadonnées, avant toute écriture sur le disque
        try:
            comfy = ComfyUIImage(image)
            positive_prompt = comfy.get_positive_prompt()
        except ValueError as err:
            flash(f"Import impossible : {err}", "error")
            return redirect(url_for('.add'))
        except OSError:
            flash("Fichier image illisible.", "error")
            return redirect(url_for('.add'))

        # Construction du nom de l'image optimisée
        filename = f"{uuid.uuid4().hex}.webp"
        path_filename = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                     filename)

        try:
            comfy.optimize_image(path_filename)
            image_hash = get_file_hash(path_filename)

            if Prompt.query.filter_by(image_hash=image_hash).first():
                os.remove(path_filename)
                flash("Le prompt existe déjà dans la base", "error")
                return redirect(url_for('.index'))

            else:
                # conversion de l'image en webp

                new_prompt = Prompt(
                    prompt=positive_prompt,
                    tags=tags_cleaned,
                    image_filename=filename,
                    seed=comfy.get_seed(),
                    steps=comfy.get_steps(),
                    checkpoint=comfy.get_checkpoint(),
                    loras=comfy.get_loras(),
                    neg_prompt=comfy.get_negative_prompt(),
                    cfg=comfy.get_cfg(),
                    prompt_raw=comfy.get_prompt_raw(),
                    sampler=comfy.get_sampler(),
                    scheduler=comfy.get_scheduler(),
                    category_id=categorie_id,
                    image_hash=image_hash,
                )
                db.session.add(new_prompt)
                db.session.commit()

        except (OSError, ValueError, SQLAlchemyError):
            db.session.rollback()
            if os.path.exists(path_filename):
                os.remove(path_filename)
            current_app.logger.exception("Échec de l'ajout d'un prompt")
            flash("Erreur lors de l'ajout du prompt.", "error")
            return redirect(url_for('.add'))

        current_app.logger.debug("Prompt %s ajouté (hash %s)",
                                 new_prompt.id, image_hash)

        flash("Prompt ajouté avec succès.", "success")
        return redirect(url_for('.index'))

    return render_template('add.html',
                           liste_categories=category_options,
                           app_version=__version__)


@prompt_bp.route('/edit/<int:prompt_id>', methods=['GET', 'POST'])
def edit(prompt_id):

    """
    Modifie un prompt existant (catégorie, tags, image).
    :param prompt_id: ID du prompt à modifier
    """

    prompt = db.get_or_404(Prompt, prompt_id)
    category_options = CategoryService.get_category_options()

    if request.method == 'POST':
        prompt.tags = clean_tags(request.form.get('tags', ''))
        prompt.category_id = request.form.get('categorie') or None

        image = request.files.get('image')
        old_filename = None

        if image and image.filename:
            if not allowed_file(image.filename):
                flash("Format d'image non autorisé.", "error")
                return redirect(request.url)

            new_filename = f"{uuid.uuid4().hex}.webp"
            new_path = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    new_filename)
            try:
                save_webp(image, new_path)
            except (OSError, ValueError):
                flash("Image invalide.", "error")
                return redirect(request.url)

            new_hash = get_file_hash(new_path)
            duplicate = Prompt.query.filter(
                Prompt.image_hash == new_hash,
                Prompt.id != prompt.id
            ).first()
            if duplicate:
                os.remove(new_path)
                flash("Cette image existe déjà dans la base.", "error")
                return redirect(request.url)

            old_filename = prompt.image_filename
            prompt.image_filename = new_filename
            prompt.image_hash = new_hash

        db.session.commit()

        # Suppression de l'ancienne image seulement après le commit
        if old_filename:
            try:
                os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'],
                                       old_filename))
            except FileNotFoundError:
                pass

        flash("Prompt modifié.", "success")
        return redirect(url_for('.view', prompt_id=prompt.id))

    return render_template('edit.html', prompt=prompt,
                           liste_categories=category_options)


@prompt_bp.route('/delete/<int:prompt_id>', methods=['POST'])
def delete(prompt_id):

    """
    Supprime un prompt et son image associée (si présente).
    :param prompt_id: ID du prompt à supprimer
    """

    prompt = Prompt.query.get_or_404(prompt_id)
    if prompt.image_filename:
        try:
            os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'],
                                   prompt.image_filename))
        except FileNotFoundError:
            pass
    db.session.delete(prompt)
    db.session.commit()
    flash("Prompt supprimé.", "info")
    return redirect(url_for('.index'))


# Route pour créer une nouvelle catégorie
@prompt_bp.route('/categories/new', methods=['GET', 'POST'])
def new_category():
    """Ajout d'une catégrorie"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '')
        parent_id = request.form.get('parent_id', type=int)

        if not name:
            flash('Le nom de la catégorie est requis', 'error')
            return redirect(request.url)

        category = Category(
            name=name,
            description=description,
            parent_id=parent_id
        )

        db.session.add(category)
        db.session.commit()

        flash(f'Catégorie "{name}" créée avec succès!', 'success')
        return redirect(url_for('prompt.manage_categories'))

    # Pour le formulaire GET
    category_options = CategoryService.get_category_options()
    return render_template('category_form.html',
                           category_options=category_options,
                           title="Nouvelle catégorie")


# Route pour éditer une catégorie
@prompt_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    """Edite un catégorie"""
    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Le nom de la catégorie est requis', 'error')
            return redirect(request.url)

        category.name = name
        category.description = request.form.get('description', '')

        # None si "Aucune catégorie" ou valeur invalide
        new_parent_id = request.form.get('parent_id', type=int)

        # Vérifier si le changement de parent est valide
        if new_parent_id != category.parent_id:
            try:
                CategoryService.move_category(category.id, new_parent_id)
            except ValueError as err:
                db.session.rollback()
                flash(str(err), 'error')
                return redirect(request.url)

        db.session.commit()
        flash('Catégorie mise à jour avec succès!', 'success')
        return redirect(url_for('prompt.manage_categories'))

    # Exclure la catégorie elle-même et ses descendants des options parent
    category_options = [('', '-- Aucune catégorie --')]

    def add_valid_options(categories, level=0):
        for cat in categories:
            if cat.id != category.id and not category.is_ancestor_of(cat):
                indent = "　" * level
                category_options.append((cat.id, f"{indent}{cat.name}"))
                add_valid_options(cat.children.all(), level + 1)

    root_categories = Category.query.filter_by(parent_id=None).all()
    add_valid_options(root_categories)

    return render_template('category_form.html',
                           category=category,
                           category_options=category_options,
                           title="Modifier la catégorie")


# Route pour supprimer une catégorie
@prompt_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    """Supprime une catégorie"""
    category = Category.query.get_or_404(category_id)

    # Vérifier s'il y a des prompts ou des sous-catégories
    prompts_count = category.prompts.count()
    children_count = category.children.count()

    if prompts_count > 0 or children_count > 0:
        flash(
            f'Impossible de supprimer "{category.name}": elle contient '
            f'{prompts_count} prompt(s) et {children_count} sous-catégorie(s)',
            'error')
        return redirect(url_for('prompt.manage_categories'))

    db.session.delete(category)
    db.session.commit()

    flash(f'Catégorie "{category.name}" supprimée avec succès!', 'success')
    return redirect(url_for('prompt.manage_categories'))


# Route pour gérer toutes les catégories
@prompt_bp.route('/categories')
def manage_categories():
    """Gestion des catégories"""
    return render_template('manage_categories.html')


# API pour l'arbre des catégories (pour JavaScript)
@prompt_bp.route('/api/categories/tree')
def api_categories_tree():
    """API pour l'arbre des catégories (pour JavaScript)"""
    root_categories = CategoryService.get_tree()
    tree = [CategoryService.build_tree_dict(cat) for cat in root_categories]
    return jsonify(tree)

# -----------------------------------------------------------------------------------


@prompt_bp.route('/statistiques')
def statistiques():
    """Génére toutes les elements pour le panneau des statistiques"""

    # Recuperation des checkpoints
    nbr_prompts = Prompt.query.count()

    results_checkpoints = (
        db.session.query(
            Prompt.checkpoint,
            func.count(Prompt.checkpoint).label("count"),
        )
        .filter(Prompt.checkpoint.isnot(None))
        .group_by(Prompt.checkpoint)
        .order_by(func.count(Prompt.checkpoint).desc())
        .all()
    )
    # Recuperation des Loras
    result_loras = db.session.query(Prompt.loras).all()

    counter = Counter(
        lora
        for (loras_dict,) in result_loras
        if loras_dict
        for lora in loras_dict
    )

    results_loras = sorted(
        counter.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Recupeartion des Tags
    all_tags = Counter(
        tag.strip().lower()
        for (tags,) in db.session.query(Prompt.tags).all()
        for tag in (tags or '').split(',')
        if tag.strip()
    )

    results_tags = sorted(
        all_tags.items(),
        key=lambda x: x[1],
        reverse=True
    )

    # Recuperation de la taille du dossier des images
    taille_upload_folder = taille_path(current_app.config['UPLOAD_FOLDER'])
    # Recuperation de la taille de la bdd
    taille_bdd = taille_path(current_app.config['DB_PATH'])

    current_app.logger.debug(
        "Stats : %d checkpoints, %d loras, %d tags",
        len(results_checkpoints), len(results_loras), len(results_tags))

    return render_template('statistiques.html',
                           nbr_prompts=nbr_prompts,
                           list_checkpoints=results_checkpoints,
                           loras=results_loras,
                           list_tags=results_tags,
                           taille_bdd=taille_bdd,
                           taille_upload_folder=taille_upload_folder)
