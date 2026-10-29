from flask import Blueprint, jsonify, redirect, session, url_for

from .decorators import is_login
from .extensions import db
from .models import User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return redirect(url_for('auth.login'))


@main_bp.route('/dashboard', methods=['GET'])
@is_login
def dashboard():
    user = db.session.get(User, session['id'])
    if user is None:
        session.clear()
        return jsonify({'message': "Login required to proceed"}), 401
    return jsonify({'message': f"Welcome, {user.username}"}), 200