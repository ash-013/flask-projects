from flask import Blueprint, current_app, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash
from .decorators import is_login
from .extensions import db
from .models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'id' in session:
            return redirect(url_for('main.dashboard'))
        return render_template('login_page.html')

    wants_json = request.is_json
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    def fail(message, status):
        if wants_json:
            return jsonify({'message': message}), status
        return render_template('login_page.html', error=message, username=username), status

    if not username:
        return fail("Username cannot be blank", 400)
    if not password:
        return fail("Password cannot be blank", 400)

    try:
        user = db.session.execute(
            db.select(User).filter_by(username=username)
        ).scalar_one_or_none()
    except SQLAlchemyError:
        current_app.logger.exception("Database error during login")
        return fail("Something went wrong. Please try again.", 500)

    if user is None or not check_password_hash(user.password, password):
        return fail("Invalid username or password", 401)

    session.clear()
    session['id'] = user.id
    session.permanent = True

    if wants_json:
        return jsonify({'message': "Login successful"}), 200
    return redirect(url_for('main.dashboard'))


@auth_bp.route('/logout', methods=['POST'])
@is_login
def logout():
    session.clear()
    return jsonify({'message': "Logged out"}), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json(silent=True) or request.form
    username = (data.get('username') or '').strip()
    email = (data.get('email') or '').strip().lower()
    password = data.get('password') or ''

    if not username:
        return jsonify({'message': "Username cannot be blank"}), 400
    if not email:
        return jsonify({'message': "Email cannot be blank"}), 400
    if not password.strip():
        return jsonify({'message': "Password cannot be blank"}), 400
    if len(username) > 255 or len(email) > 255:
        return jsonify({'message': "Username or email is too long"}), 400
    if '@' not in email:
        return jsonify({'message': "Invalid email address"}), 400
    if len(password) < 8:
        return jsonify({'message': "Password must be at least 8 characters"}), 400

    user = User(
        username=username,
        email=email,
        password=generate_password_hash(password),
    )
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': "Username or email already exists"}), 409

    return jsonify({'message': "Registration successful"}), 201