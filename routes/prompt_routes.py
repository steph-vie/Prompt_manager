"""Liste de toutes les routes de l'application"""

import os
import uuid
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app, jsonify
)
from werkzeug.utils import secure_filename

from models import db, Prompt, Category
from utils import ComfyUIImage, allowed_file, clean_tags, CategoryService
from sqlalchemy import func
from collections import Counter

prompt_bp = Blueprint('prompt', __name__)


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
            (Prompt.title.contains(query)) | (Prompt.prompt.contains(query))
        )

    pagination = prompts_query.order_by(Prompt.id.desc()).paginate(page=page,
                                                                   per_page=12)
    prompts = pagination.items

    all_tags = set(
        tag.strip()
        for p in Prompt.query.all()
        for tag in (p.tags or '').split(',')
    )

    # Récupérer l'arbre des catégories pour la sidebar
    category_tree = CategoryService.get_tree()

    return render_template('index.html',
                           prompts=prompts,
                           tags=sorted(all_tags),
                           selected_tag=tag,
                           query=query or '',
                           pagination=pagination,
                           category_tree=category_tree,
                           selected_category=selected_category)


@prompt_bp.route('/prompt/<int:prompt_id>')
def view(prompt_id):

    """
    Affiche les détails d’un prompt spécifique.
    :param prompt_id: ID du prompt à afficher
    """

    prompt = Prompt.query.get_or_404(prompt_id)
    category_tree = CategoryService.get_tree()
    all_tags = set(
        tag.strip()
        for p in Prompt.query.all()
        for tag in (p.tags or '').split(',')
    )
    return render_template('view.html',
                           prompt=prompt,
                           category_tree=category_tree,
                           tags=sorted(all_tags))


@prompt_bp.route('/add', methods=['GET', 'POST'])
def add():

    """
    Ajoute un nouveau prompt à la base de données.
    Accepte un formulaire avec un titre, un prompt, des tags et une image.
    """
    category_options = CategoryService.get_category_options()
    if request.method == 'POST':
        title = request.form['title']
        tags = request.form['tags']
        categorie_id = request.form['categorie']

        if not title.strip():
            flash("Le titre est obligatoire.", "error")
            return redirect(url_for('.add'))

        tags_cleaned = clean_tags(tags)
        image = request.files['image']
        filename = None

        if image and allowed_file(image.filename):
            ext = os.path.splitext(image.filename)[1]
            filename = secure_filename(f"{uuid.uuid4().hex}{ext}")
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    filename))
        image_upload = ComfyUIImage(os.path.
                                    join(current_app.config['UPLOAD_FOLDER'],
                                         filename))
        new_prompt = Prompt(title=title,
                            prompt=image_upload.get_positive_prompt(),
                            tags=tags_cleaned,
                            image_filename=filename,
                            seed=image_upload.get_seed(),
                            steps=image_upload.get_steps(),
                            checkpoint=image_upload.get_checkpoint(),
                            loras=str(image_upload.get_loras()),
                            neg_prompt=image_upload.get_negative_prompt(),
                            category_id=categorie_id
                            )
        db.session.add(new_prompt)
        db.session.commit()
        flash("Prompt ajouté avec succès.", "success")
        return redirect(url_for('.index'))

    return render_template('add.html', liste_categories=category_options)


@prompt_bp.route('/edit/<int:prompt_id>', methods=['GET', 'POST'])
def edit(prompt_id):

    """
    Modifie un prompt existant.
    Permet de changer le titre, le contenu, les tags et l’image.
    :param prompt_id: ID du prompt à modifier
    """

    prompt = Prompt.query.get_or_404(prompt_id)
    category_options = CategoryService.get_category_options()
    if request.method == 'POST':
        prompt.title = request.form['title']
        # prompt.prompt = request.form['prompt']
        prompt.tags = clean_tags(request.form['tags'])
        prompt.category_id = request.form['categorie']

        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    filename))
            prompt.image_filename = filename

        db.session.commit()
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
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        parent_id = request.form.get('parent_id') or None

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
    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description', '')
        new_parent_id = request.form.get('parent_id') or None

        # Vérifier si le changement de parent est valide
        if new_parent_id and int(new_parent_id) != category.parent_id:
            try:
                CategoryService.move_category(category.id, new_parent_id)
                flash('Catégorie mise à jour avec succès!', 'success')
            except ValueError as e:
                flash(str(e), 'error')
                return redirect(request.url)
        else:
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
    category = Category.query.get_or_404(category_id)

    # Vérifier s'il y a des prompts ou des sous-catégories
    prompts_count = category.prompts.count()
    children_count = category.children.count()

    if prompts_count > 0 or children_count > 0:
        flash(
            f'Impossible de supprimer "{category.name}": elle contient {prompts_count} prompt(s) et {children_count} sous-catégorie(s)',
            'error')
        return redirect(url_for('prompt.manage_categories'))

    db.session.delete(category)
    db.session.commit()

    flash(f'Catégorie "{category.name}" supprimée avec succès!', 'success')
    return redirect(url_for('prompt.manage_categories'))


# Route pour gérer toutes les catégories
@prompt_bp.route('/categories')
def manage_categories():
    category_tree = CategoryService.get_tree()
    return render_template('manage_categories.html',
                           category_tree=category_tree)


# API pour l'arbre des catégories (pour JavaScript)
@prompt_bp.route('/api/categories/tree')
def api_categories_tree():
    root_categories = CategoryService.get_tree()
    tree = [CategoryService.build_tree_dict(cat) for cat in root_categories]
    return jsonify(tree)

# -----------------------------------------------------------------------------------


@prompt_bp.route('/statistiques')
def statistiques():

    # Recuperation des checkpoints
    nbr_prompts = Prompt.query.count()
    results_checkpoints = (
    db.session.query(
        Prompt.checkpoint,
        func.count(Prompt.checkpoint).label("count")
    )
    .group_by(Prompt.checkpoint)
    .order_by(func.count(Prompt.checkpoint).desc())  # tri décroissant par occurrence
    .all()
)
    # Convertir en vrais tuples
    results_checkpoints = [(r.checkpoint, r.count) for r in results_checkpoints]

    # Recuperation des Loras
    result_loras = db.session.query(Prompt.loras).all()
    loras_sorted = dict(sorted(
        Counter(
            lora.strip()
            for loras_per_prompt in result_loras
            for loras in loras_per_prompt
            for lora in str(loras).split(",")
            if lora.strip() and lora.strip() != "None"
        ).items(),
        key=lambda x: x[1],
        reverse=True
    ))
    results_loras = [(k, v) for k, v in loras_sorted.items()]

    # Recuperation du nbr de tags
    all_tags = db.session.query(Prompt.tags).all()

    dict_tags = dict(sorted(
        Counter(
            t.strip()
            for tag in all_tags
            for p in tag
            for t in p.split(",")
        ).items(),
        key=lambda x: x[1],
        reverse=True))

    results_tags = [(k, v) for k, v in dict_tags.items()]

    return render_template('statistiques.html',
                           nbr_prompts=nbr_prompts,
                           list_checkpoints=results_checkpoints,
                           loras=results_loras,
                           list_tags=results_tags)


@prompt_bp.route('/historique')
def historique():

    return render_template('historique.html')
