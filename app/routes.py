# app/routes.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Application

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
