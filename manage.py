from flask.cli import FlaskGroup
from app import create_app, db

# The app factory pattern
def create():
    return create_app()

cli = FlaskGroup(create_app=create)

if __name__ == "__main__":
    cli()
