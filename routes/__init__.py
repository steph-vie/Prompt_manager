from .prompt_routes import prompt_bp


def register_routes(app):
    app.register_blueprint(prompt_bp)
