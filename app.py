from flask import Flask, request, jsonify, session, send_from_directory
from db.database import get_db, init_database
from db.models import User
from auth import hash_password, verify_password
from game_logic import evaluate_guess, is_valid_word, VALID_WORDS
import secrets
import random

# Flask app setup
app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secret key for sessions

# Game settings
MAX_GUESSES = 6
WORD_LENGTH = 5  # classic Wordle

# Initialize database on startup (creates tables if they don't exist)
init_database()
print("Database initialized - tables ready!")


# --------------------
# Basic routes
# --------------------
@app.route("/")
def index():
    """Serve the main single-page app."""
    # index.html lives in the project root
    return send_from_directory("templates", "index.html")


@app.route("/singleplayer")
def singleplayer_page():
    """Serve the single-player game page."""
    return send_from_directory("templates", "singleplayer.html")


# --------------------
# Auth API
# --------------------
@app.route("/api/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    # Validation
    if not username or not password:
        return (
            jsonify(
                {"success": False, "error": "Username and password are required"}
            ),
            400,
        )

    if len(username) < 3 or len(username) > 20:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Username must be between 3 and 20 characters",
                }
            ),
            400,
        )

    if len(password) < 4:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "Password must be at least 4 characters",
                }
            ),
            400,
        )

    db_gen = get_db()
    db = next(db_gen)

    try:
        # Check for existing username
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            return (
                jsonify({"success": False, "error": "Username already exists"}),
                400,
            )

        # Create new user
        password_hash = hash_password(password)
        new_user = User(username=username, password_hash=password_hash)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        # Set session
        session["user_id"] = new_user.id
        session["username"] = new_user.username

        user_data = {
            "id": new_user.id,
            "username": new_user.username,
            "wins": getattr(new_user, "wins", 0),
            "losses": getattr(new_user, "losses", 0),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Account created successfully",
                    "user": user_data,
                }
            ),
            201,
        )

    except Exception:
        db.rollback()
        return (
            jsonify({"success": False, "error": "Failed to create account"}),
            500,
        )

    finally:
        # Close the generator / DB session
        try:
            next(db_gen, None)
        except StopIteration:
            pass


@app.route("/api/login", methods=["POST"])
def login():
    """Log in an existing user."""
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return (
            jsonify(
                {"success": False, "error": "Username and password are required"}
            ),
            400,
        )

    db_gen = get_db()
    db = next(db_gen)

    try:
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(user.password_hash, password):
            return (
                jsonify(
                    {"success": False, "error": "Invalid username or password"}
                ),
                401,
            )

        session["user_id"] = user.id
        session["username"] = user.username

        user_data = {
            "id": user.id,
            "username": user.username,
            "wins": getattr(user, "wins", 0),
            "losses": getattr(user, "losses", 0),
        }

        return (
            jsonify(
                {
                    "success": True,
                    "message": "Logged in successfully",
                    "user": user_data,
                }
            ),
            200,
        )
    finally:
        try:
            next(db_gen, None)
        except StopIteration:
            pass


@app.route("/api/logout", methods=["POST"])
def logout():
    """Log out the current user."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out"}), 200


@app.route("/api/check-auth", methods=["GET"])
def check_auth():
    """Return whether a user is logged in, plus basic stats."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 200

    db_gen = get_db()
    db = next(db_gen)

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"authenticated": False}), 200

        user_data = {
            "id": user.id,
            "username": user.username,
            "wins": getattr(user, "wins", 0),
            "losses": getattr(user, "losses", 0),
        }
        return jsonify({"authenticated": True, "user": user_data}), 200
    finally:
        try:
            next(db_gen, None)
        except StopIteration:
            pass


# --------------------
# Single-player game API
# --------------------
@app.route("/api/new-game", methods=["POST"])
def new_game():
    """Start a new single-player Wordle game for the logged-in user."""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    # Choose a random target word of the right length from the valid list
    candidates = [w for w in VALID_WORDS if len(w) == WORD_LENGTH]
    if not candidates:
        return (
            jsonify(
                {
                    "success": False,
                    "error": "No valid words available on server",
                }
            ),
            500,
        )

    target = random.choice(candidates)  # words are uppercase in VALID_WORDS

    # Store game state in the session
    session["game"] = {
        "target": target,
        "guesses": [],
        "status": "in_progress",
    }

    return (
        jsonify(
            {
                "success": True,
                "message": "New game started",
                "max_guesses": MAX_GUESSES,
                "word_length": WORD_LENGTH,
            }
        ),
        200,
    )


@app.route("/api/guess", methods=["POST"])
def make_guess():
    """Submit a guess for the current single-player game."""
    if "user_id" not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    game = session.get("game")
    if not game or game.get("status") != "in_progress":
        return jsonify({"success": False, "error": "No active game"}), 400

    data = request.get_json() or {}
    guess_raw = (data.get("guess") or "").strip()
    guess = guess_raw.upper()

    # Basic validation
    if len(guess) != WORD_LENGTH:
        return (
            jsonify(
                {
                    "success": False,
                    "error": f"Guess must be {WORD_LENGTH} letters",
                }
            ),
            400,
        )

    if not is_valid_word(guess):
        return jsonify({"success": False, "error": "Not in word list"}), 400

    target = game["target"]
    feedback = evaluate_guess(target, guess)

    # Record the guess
    guesses = game.get("guesses", [])
    guesses.append({"guess": guess, "feedback": feedback})
    game["guesses"] = guesses

    # Win / lose logic
    won = guess == target
    lost = len(guesses) >= MAX_GUESSES and not won

    if won:
        game["status"] = "won"
    elif lost:
        game["status"] = "lost"

    session["game"] = game  # save back into session

    # If game ended, update the user's win/loss counters
    result = None
    if won or lost:
        db_gen = get_db()
        db = next(db_gen)
        try:
            user = db.query(User).filter(User.id == session["user_id"]).first()
            if user:
                if won:
                    if getattr(user, "wins", None) is not None:
                        user.wins += 1
                    result = "win"
                else:
                    if getattr(user, "losses", None) is not None:
                        user.losses += 1
                    result = "loss"
                db.commit()
        except Exception:
            db.rollback()
        finally:
            try:
                next(db_gen, None)
            except StopIteration:
                pass

    return (
        jsonify(
            {
                "success": True,
                "feedback": feedback,  # e.g. ["correct","present","miss",...]
                "guesses": guesses,    # full history of guesses + feedback
                "status": game["status"],  # "in_progress", "won", or "lost"
                "result": result,      # "win", "loss", or None
                "target": target if (won or lost) else None,
            }
        ),
        200,
    )


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
