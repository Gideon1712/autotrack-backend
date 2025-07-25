from flask.cli import FlaskGroup
from app import create_app, db
from flask_migrate import Migrate
import os

app = create_app()
migrate = Migrate(app, db)

cli = FlaskGroup(app=app)

if __name__ == "__main__":
    cli()
