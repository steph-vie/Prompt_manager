import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = 'toto'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prompts.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class Prompt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    tags = db.Column(db.String(120), nullable=True)
    image_filename = db.Column(db.String(120), nullable=True)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    tag = request.args.get('tag')
    query = request.args.get('q')

    prompts = Prompt.query
    if tag:
        prompts = prompts.filter(Prompt.tags.like(f'%{tag}%'))
    if query:
        prompts = prompts.filter((Prompt.title.contains(query)) | (Prompt.prompt.contains(query)))
    prompts = prompts.order_by(Prompt.id.desc()).all()

    tags = sorted(set(tag for p in Prompt.query.all() for tag in (p.tags or '').split(',')))
    return render_template('index.html', prompts=prompts, tags=tags, selected_tag=tag, query=query or '')

@app.route('/prompt/<int:prompt_id>')
def view(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    return render_template('view.html', prompt=prompt)

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        title = request.form['title']
        prompt_text = request.form['prompt']
        tags = request.form['tags']
        image = request.files['image']

        filename = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        new_prompt = Prompt(title=title, prompt=prompt_text, tags=tags, image_filename=filename)
        db.session.add(new_prompt)
        db.session.commit()
        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/edit/<int:prompt_id>', methods=['GET', 'POST'])
def edit(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    if request.method == 'POST':
        prompt.title = request.form['title']
        prompt.prompt = request.form['prompt']
        prompt.tags = request.form['tags']

        image = request.files['image']
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            prompt.image_filename = filename

        db.session.commit()
        return redirect(url_for('view', prompt_id=prompt.id))

    return render_template('edit.html', prompt=prompt)

@app.route('/delete/<int:prompt_id>', methods=['POST'])
def delete(prompt_id):
    prompt = Prompt.query.get_or_404(prompt_id)
    if prompt.image_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], prompt.image_filename))
        except FileNotFoundError:
            pass
    db.session.delete(prompt)
    db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
