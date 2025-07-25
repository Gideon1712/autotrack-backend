from flask_migrate import Migrate
from flask.cli import FlaskGroup
from app import create_app, db

# Create app
app = create_app()

# Bind Migrate to app and db
migrate = Migrate(app, db)

# Register Flask CLI group
cli = FlaskGroup(app=app)  # ✅ NOT create_app=create_app

# Expose CLI when this file is run
if __name__ == '__main__':
    cli()
