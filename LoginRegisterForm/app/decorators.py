from functools import wraps
from flask import jsonify, session

def is_login(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'id' not in session:
            return jsonify({'message': "Login required to proceed"}), 401
        return f(*args, **kwargs)
    return decorated_function