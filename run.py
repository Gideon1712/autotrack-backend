from flask_migrate import Migrate, MigrateCommand
from flask.cli import FlaskGroup
from app import create_app, db
import click

app = create_app()
migrate = Migrate(app, db)

# ✅ Custom CLI Group with `db` command registered
@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Management script for the Flask application."""
    pass



if __name__ == '__main__':
    cli()  # ✅ This registers `flask db` commands
