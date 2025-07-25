from flask import Flask
from flask_migrate import Migrate
from app import create_app, db  # ⬅️ import db from __init__.py

app = create_app()
migrate = Migrate(app, db)  # ⬅️ Connect migrate to app and db

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
