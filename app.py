import os
from datetime import datetime
import uuid
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

# Extensions de fichiers autorisées pour les images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialisation de l'application Flask et configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'toto'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prompts.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

# Création du dossier d'upload s'il n'existe pas
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


class Prompt(db.Model):
     """
    Modèle représentant un prompt dans la base de données.
    Contient un titre, le texte du prompt, des tags, un fichier image associé et une date de création.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(120), nullable=True)
    image_filename = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Prompt {self.title}>'

# Création de la base de données avec les tables si elles n'existent pas encore
with app.app_context():
    db.create_all()


def allowed_file(filename):
    """
    Vérifie si le fichier a une extension autorisée.
    :param filename: Nom du fichier
    :return: Booléen indiquant si le fichier est autorisé
    """
    return ('.' in filename
            and filename.rsplit('.', 1)[1].lower()
            in ALLOWED_EXTENSIONS)


@app.route('/')
def index():
    """
    Route principale affichant la liste des prompts.
    Prend en compte les filtres par tag ou par requête de recherche.
    """
    tag = request.args.get('tag')
    query = request.args.get('q')

    prompts = Prompt.query
    if tag:
        prompts = prompts.filter(Prompt.tags.like(f'%{tag}%'))
    if query:
        prompts = (
            prompts.filter((Prompt.title.contains(query))
                           | (Prompt.prompt.contains(query)))
        )
    prompts = prompts.order_by(Prompt.id.desc()).all()

    all_tags = (
        tag
        for p in Prompt.query.all()
        for tag in (p.tags or '').split(',')
    )
    tags = sorted(set(all_tags))

    return render_template('index.html',
                           prompts=prompts,
                           tags=tags,
                           selected_tag=tag,
                           query=query or '')


@app.route('/prompt/<int:prompt_id>')
def view(prompt_id):
    """
    Affiche les détails d’un prompt spécifique.
    :param prompt_id: ID du prompt à afficher
    """
    prompt = Prompt.query.get_or_404(prompt_id)
    return render_template('view.html', prompt=prompt)


@app.route('/add', methods=['GET', 'POST'])
def add():
    """
    Ajoute un nouveau prompt à la base de données.
    Accepte un formulaire avec un titre, un prompt, des tags et une image.
    """
    if request.method == 'POST':
        title = request.form['title']
        prompt_text = request.form['prompt']
        tags = request.form['tags']
        # Nettoyage des tags
        tags_clean = ','.join([tag.strip().lower() for tag in tags.split(',')])
        image = request.files['image']

        filename = None
        if image and allowed_file(image.filename):
            ext = os.path.splitext(image.filename)[1]
            filename = secure_filename(f"{uuid.uuid4().hex}{ext}")
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_prompt = Prompt(title=title,
                            prompt=prompt_text,
                            tags=tags_clean,
                            image_filename=filename)
        db.session.add(new_prompt)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add.html')


@app.route('/edit/<int:prompt_id>', methods=['GET', 'POST'])
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
        tags = request.form['tags']
        # Nettoyage des tags
        tags_clean = ','.join([tag.strip().lower() for tag in tags.split(',')])
        prompt.tags = tags_clean

        image = request.files['image']
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            prompt.image_filename = filename

        db.session.commit()
        return redirect(url_for('view', prompt_id=prompt.id))

    return render_template('edit.html', prompt=prompt)


@app.route('/delete/<int:prompt_id>', methods=['POST'])
def delete(prompt_id):
    """
    Supprime un prompt et son image associée (si présente).
    :param prompt_id: ID du prompt à supprimer
    """
    prompt = Prompt.query.get_or_404(prompt_id)
    if prompt.image_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'],
                                   prompt.image_filename))
        except FileNotFoundError:
            pass
    db.session.delete(prompt)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Lance l’application Flask en mode debug
    app.run(debug=True)
