from flask_migrate import Migrate
from flask.cli import with_appcontext
from app import create_app, db

app = create_app()
migrate = Migrate(app, db)

# Optional: define CLI context for shell access (optional but useful)
@app.shell_context_processor
def make_shell_context():
    return {'db': db}
