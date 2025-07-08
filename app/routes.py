from flask import Blueprint, request, jsonify, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Application
import boto3
import os
import uuid
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

# ----------------- HTML VIEWS -----------------
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/signup', methods=['GET'])
def signup_form():
    return render_template('signup.html')

@main.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')

@main.route('/dashboard/<int:user_id>', methods=['GET'])
def dashboard(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
    return render_template('dashboard.html', user_id=user_id)

# ----------------- SIGNUP & LOGIN -----------------
@main.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']
    hashed_pw = generate_password_hash(password, method='sha256')
    user = User(email=email, password=hashed_pw)
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('main.login_form'))

@main.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        return redirect(url_for('main.dashboard', user_id=user.id))
    return render_template('login.html', error="Invalid credentials")

# ----------------- APPLICATION ROUTES (JSON API) -----------------
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

# ----------------- RESUME UPLOAD FORM + LOGIC -----------------
@main.route('/upload_resume', methods=['POST'])
def upload_resume():
    if 'file' not in request.files:
        return "No file uploaded", 400

    file = request.files['file']
    if file.filename == '':
        return "Empty filename", 400

    user_id = request.form.get('user_id')
    company = request.form.get('company')
    position = request.form.get('position')
    status = request.form.get('status', 'Applied')
    notes = request.form.get('notes', '')

    if not all([user_id, company, position]):
        return "Missing fields", 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[-1]
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    bucket_name = os.getenv('S3_BUCKET')
    region = os.getenv('S3_REGION')

    try:
        s3 = boto3.client('s3', region_name=region)
        s3.upload_fileobj(file, bucket_name, unique_filename)
        file_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"

        application = Application(
            company=company,
            position=position,
            status=status,
            notes=notes,
            user_id=int(user_id),
            resume_url=file_url
        )
        db.session.add(application)
        db.session.commit()

        return redirect(url_for('main.dashboard', user_id=user_id))
    except Exception as e:
        db.session.rollback()
        return f"Upload failed: {e}", 500

