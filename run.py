# run.py
from flask_migrate import Migrate
from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()
migrate = Migrate(app, db)

cli = FlaskGroup(create_app=create_app)  # correct linkage to factory

if __name__ == '__main__':
    cli()  # NOT app.run() — this enables `flask db` commands
