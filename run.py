from flask import Flask, send_from_directory
from app import create_app

app = create_app()

@app.route('/')
def serve_frontend():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def serve_static_file(path):
    return send_from_directory('frontend', path)

if __name__ == "__main__":
    app.run()
