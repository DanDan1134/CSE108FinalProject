from flask import Flask, render_template, request, jsonify, session
from db.database import get_db, init_database
from db.models import User
from auth import hash_password, verify_password
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secret key for sessions

# Initialize database on startup (creates tables if they don't exist)
init_database()
print("Database initialized - tables ready!")


@app.route('/')
def index():
    """Serve the main game page"""
    return render_template('index.html')


@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    # Validation
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password are required'}), 400
    
    if len(username) < 3 or len(username) > 20:
        return jsonify({'success': False, 'error': 'Username must be between 3 and 20 characters'}), 400
    
    if len(password) < 4:
        return jsonify({'success': False, 'error': 'Password must be at least 4 characters'}), 400
    
    # Check if username already exists
    db_gen = get_db()
    db = next(db_gen)
    existing_user = db.query(User).filter(User.username == username).first()
    
    if existing_user:
        next(db_gen, None)  # Close the generator
        return jsonify({'success': False, 'error': 'Username already exists'}), 400
    
    # Create new user
    try:
        password_hash = hash_password(password)
        new_user = User(username=username, password_hash=password_hash)
        db.add(new_user)
        db.commit()
        user_id = new_user.id
        next(db_gen, None)  # Close the generator
        
        # Set session
        session['user_id'] = user_id
        session['username'] = username
        
        return jsonify({
            'success': True,
            'message': 'Account created successfully',
            'user': {'id': user_id, 'username': username}
        }), 201
    except Exception as e:
        db.rollback()
        next(db_gen, None)  # Close the generator
        return jsonify({'success': False, 'error': 'Failed to create account'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """Login a user"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    # Validation
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password are required'}), 400
    
    # Find user
    db_gen = get_db()
    db = next(db_gen)
    user = db.query(User).filter(User.username == username).first()
    
    if not user:
        next(db_gen, None)  # Close the generator
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
    
    # Verify password
    if not verify_password(user.password_hash, password):
        next(db_gen, None)  # Close the generator
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401
    
    # Set session
    session['user_id'] = user.id
    session['username'] = user.username
    
    user_data = {'id': user.id, 'username': user.username, 'wins': user.wins, 'losses': user.losses}
    next(db_gen, None)  # Close the generator
    
    return jsonify({
        'success': True,
        'message': 'Login successful',
        'user': user_data
    }), 200


@app.route('/api/logout', methods=['POST'])
def logout():
    """Logout the current user"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200


@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    if 'user_id' in session:
        db_gen = get_db()
        db = next(db_gen)
        user = db.query(User).filter(User.id == session['user_id']).first()
        
        if user:
            user_data = {'id': user.id, 'username': user.username, 'wins': user.wins, 'losses': user.losses}
            next(db_gen, None)  # Close the generator
            return jsonify({
                'authenticated': True,
                'user': user_data
            }), 200
        next(db_gen, None)  # Close the generator
    
    return jsonify({'authenticated': False}), 200


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)

