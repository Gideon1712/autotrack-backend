from flask_migrate import Migrate
from flask.cli import FlaskGroup
from app import create_app, db

app = create_app()
migrate = Migrate(app, db)

cli = FlaskGroup(app=app)  # ⬅ critical: pass `app=app`, not `create_app=create_app`

# Register the CLI group directly
if __name__ == "__main__":
    cli()

# ✅ This line is what lets `flask db` work
# ⬇ Make sure it's NOT inside the if __name__ block
cli()  # <-- This line is now global
