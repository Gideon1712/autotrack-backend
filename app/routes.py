from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from .models import db, User, Application
import boto3
import os
import uuid
import requests
import base64
import jwt
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

# ----------------- HTML VIEWS -----------------
@main.route('/')
def index():
    return render_template('index.html')

@main.route('/signup')
def login_signup():
    return redirect("https://eu-north-18cfqqehkz.auth.eu-north-1.amazoncognito.com/login?client_id=3rjl3gh2urarm3hqrlfi9vthmq&response_type=code&scope=email+openid+phone&redirect_uri=https://staging.d37tilv61lh248.amplifyapp.com/callback.html")

@main.route('/login')
def login_redirect():
    return redirect("https://eu-north-18cfqqehkz.auth.eu-north-1.amazoncognito.com/login?client_id=3rjl3gh2urarm3hqrlfi9vthmq&response_type=code&scope=email+openid+phone&redirect_uri=https://staging.d37tilv61lh248.amplifyapp.com/callback.html")

@main.route('/dashboard/<int:user_id>', methods=['GET'])
def dashboard(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404

    applications = Application.query.filter_by(user_id=user_id).order_by(Application.date_applied.desc()).all()
    return render_template('dashboard.html', user_id=user_id, applications=applications)


# ----------------- SIGNUP & LOGIN -----------------
@main.route('/signup', methods=['POST'])
def signup():
    email = request.form['email']
    password = request.form['password']
    hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')
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
        'resume_url': app.resume_url,
        'date_applied': app.date_applied
    } for app in applications]
    return jsonify(result), 200

@main.route('/applications/<int:id>', methods=['PUT'])
def update_application(id):
    app = Application.query.get(id)
    if not app:
        return jsonify({'message': 'Application not found'}), 404

    data = request.get_json()

    # Only allow known fields to be updated
    allowed_fields = ['status', 'notes', 'company', 'position']
    for key in allowed_fields:
        if key in data:
            setattr(app, key, data[key])

    try:
        db.session.commit()
        return jsonify({
            'message': 'Application updated successfully',
            'updated': {key: getattr(app, key) for key in allowed_fields if key in data}
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Update failed: {str(e)}'}), 500


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
    try:
        if 'file' not in request.files:
            return "No file uploaded", 400

        file = request.files['file']
        if not file or file.filename.strip() == '':
            return "Empty or invalid file", 400

        filename = secure_filename(file.filename)
        if '.' not in filename or not filename.lower().endswith('.pdf'):
            return "Only PDF files are allowed", 400

        user_id = request.form.get('user_id')
        company = request.form.get('company')
        position = request.form.get('position')
        status = request.form.get('status', 'Applied')
        notes = request.form.get('notes', '')

        if not all([user_id, company, position]):
            return "Missing required fields", 400

        ext = filename.rsplit('.', 1)[-1]
        unique_filename = f"{uuid.uuid4().hex}.{ext}"

        bucket_name = os.getenv('S3_BUCKET')
        region = os.getenv('S3_REGION')

        if not bucket_name or not region:
            return "S3 configuration missing", 500

        s3 = boto3.client('s3', region_name=region)
        s3.upload_fileobj(file, bucket_name, unique_filename)
        s3.put_object_acl(ACL='public-read', Bucket=bucket_name, Key=unique_filename)
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
        return f"Upload failed: {str(e)}", 500

# Cognito config
COGNITO_DOMAIN = "https://eu-north-18cfqqehkz.auth.eu-north-1.amazoncognito.com"
CLIENT_ID = "3rjl3gh2urarm3hqrlfi9vthmq"
CLIENT_SECRET = "o4p2ptn5m1inr7223g4iah8h44our75aiflcg26fkn5d5pvljt1"
REDIRECT_URI = "https://staging.d37tilv61lh248.amplifyapp.com/callback.html"

@main.route('/callback.html')
def oauth_callback():
    code = request.args.get('code')
    if not code:
        return "Missing code in callback", 400

    # Exchange code for tokens
    token_url = f"{COGNITO_DOMAIN}/oauth2/token"
    auth_str = f"{CLIENT_ID}:{CLIENT_SECRET}"
    b64_auth = base64.b64encode(auth_str.encode()).decode()

    headers = {
        "Authorization": f"Basic {b64_auth}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }

    token_response = requests.post(token_url, headers=headers, data=data)
    if token_response.status_code != 200:
        return f"Failed to get tokens: {token_response.text}", 400

    tokens = token_response.json()
    id_token = tokens.get("id_token")
    if not id_token:
        return "No ID token found", 400

    # Decode ID token
    decoded = jwt.decode(id_token, options={"verify_signature": False})
    user_sub = decoded.get("sub")

    if not user_sub:
        return "No user ID (sub) in token", 400

    # OPTIONAL: Map Cognito user to your DB user (if needed)
    user = User.query.filter_by(cognito_sub=user_sub).first()
    if not user:
        # If user doesn't exist, create one (you can also use email if present)
        user = User(cognito_sub=user_sub, email=decoded.get("email", "no-email@unknown.com"))
        db.session.add(user)
        db.session.commit()

    session["user_id"] = user.id
    return redirect(url_for('main.dashboard', user_id=user.id))