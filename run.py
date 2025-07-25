from flask_migrate import Migrate
from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()
migrate = Migrate(app, db)

cli = FlaskGroup(create_app=create_app)  # ✅ <-- define at top-level

# ✅ Make sure this line is present at module level (not just inside __main__)
if __name__ == '__main__':
    cli()
