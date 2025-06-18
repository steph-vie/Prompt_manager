import os
import uuid
from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app
)
from werkzeug.utils import secure_filename

from models import db, Prompt
from utils import allowed_file, clean_tags

prompt_bp = Blueprint('prompt', __name__)


@prompt_bp.route('/')
def index():

    """
    Route principale affichant la liste des prompts.
    Prend en compte les filtres par tag ou par requête de recherche.
    """

    tag = request.args.get('tag')
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)

    prompts_query = Prompt.query
    if tag:
        prompts_query = prompts_query.filter(Prompt.tags.like(f'%{tag}%'))
    if query:
        prompts_query = prompts_query.filter(
            (Prompt.title.contains(query)) | (Prompt.prompt.contains(query))
        )

    pagination = prompts_query.order_by(Prompt.id.desc()).paginate(page=page,
                                                                   per_page=10)
    prompts = pagination.items

    all_tags = set(
        tag.strip()
        for p in Prompt.query.all()
        for tag in (p.tags or '').split(',')
    )

    return render_template('index.html',
                           prompts=prompts,
                           tags=sorted(all_tags),
                           selected_tag=tag,
                           query=query or '',
                           pagination=pagination)


@prompt_bp.route('/prompt/<int:prompt_id>')
def view(prompt_id):

    """
    Affiche les détails d’un prompt spécifique.
    :param prompt_id: ID du prompt à afficher
    """

    prompt = Prompt.query.get_or_404(prompt_id)
    return render_template('view.html', prompt=prompt)


@prompt_bp.route('/add', methods=['GET', 'POST'])
def add():

    """
    Ajoute un nouveau prompt à la base de données.
    Accepte un formulaire avec un titre, un prompt, des tags et une image.
    """

    if request.method == 'POST':
        title = request.form['title']
        prompt_text = request.form['prompt']
        tags = request.form['tags']

        if not title.strip():
            flash("Le titre est obligatoire.", "error")
            return redirect(url_for('.add'))
        if not prompt_text.strip():
            flash("Le contenu est obligatoire.", "error")
            return redirect(url_for('.add'))

        tags_cleaned = clean_tags(tags)
        image = request.files['image']
        filename = None

        if image and allowed_file(image.filename):
            ext = os.path.splitext(image.filename)[1]
            filename = secure_filename(f"{uuid.uuid4().hex}{ext}")
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    filename))

        new_prompt = Prompt(title=title,
                            prompt=prompt_text,
                            tags=tags_cleaned,
                            image_filename=filename)
        db.session.add(new_prompt)
        db.session.commit()
        flash("Prompt ajouté avec succès.", "success")
        return redirect(url_for('.index'))

    return render_template('add.html')


@prompt_bp.route('/edit/<int:prompt_id>', methods=['GET', 'POST'])
def edit(prompt_id):

    """
    Modifie un prompt existant.
    Permet de changer le titre, le contenu, les tags et l’image.
    :param prompt_id: ID du prompt à modifier
    """

    prompt = Prompt.query.get_or_404(prompt_id)
    if request.method == 'POST':
        prompt.title = request.form['title']
        prompt.prompt = request.form['prompt']
        prompt.tags = clean_tags(request.form['tags'])

        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(current_app.config['UPLOAD_FOLDER'],
                                    filename))
            prompt.image_filename = filename

        db.session.commit()
        flash("Prompt modifié.", "success")
        return redirect(url_for('.view', prompt_id=prompt.id))

    return render_template('edit.html', prompt=prompt)


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
