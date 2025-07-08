# app/routes.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Application
import boto3
import os
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

@main.route('/signup', methods=['POST'])
def signup():
    data = request.json
    hashed_pw = generate_password_hash(data['password'], method='sha256')
    user = User(email=data['email'], password=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User created successfully'}), 201

@main.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@main.route('/applications', methods=['POST'])
def create_application():
    data = request.json
    app = Application(**data)
    db.session.add(app)
    db.session.commit()
    return jsonify({'message': 'Application added'}), 201

@main.route('/applications', methods=['GET'])
def list_applications():
    applications = Application.query.all()
    result = [{
        'id': app.id,
        'company': app.company,
        'position': app.position,
        'status': app.status,
        'notes': app.notes,
        'date_applied': app.date_applied
    } for app in applications]
    return jsonify(result), 200

@main.route('/applications/<int:id>', methods=['PUT'])
def update_application(id):
    data = request.json
    app = Application.query.get(id)
    if not app:
        return jsonify({'message': 'Not found'}), 404
    for key, value in data.items():
        setattr(app, key, value)
    db.session.commit()
    return jsonify({'message': 'Updated'}), 200

@main.route('/applications/<int:id>', methods=['DELETE'])
def delete_application(id):
    app = Application.query.get(id)
    if not app:
        return jsonify({'message': 'Not found'}), 404
    db.session.delete(app)
    db.session.commit()
    return jsonify({'message': 'Deleted'}), 200

@main.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to AutoTrack: Smart Job Application Tracker API!"})

@main.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filename = secure_filename(file.filename)
    bucket_name = os.getenv('S3_BUCKET')
    region = os.getenv('S3_REGION')

    try:
        s3 = boto3.client('s3', region_name=region)
        s3.upload_fileobj(file, bucket_name, filename)
        file_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{filename}"
        return jsonify({'message': 'Upload successful', 'url': file_url}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500