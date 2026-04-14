from flask import Flask, render_template, request, jsonify, session
import sqlite3
import os
import uuid
import json
import hashlib
import urllib.request
import urllib.parse
from datetime import datetime
from collections import Counter

app = Flask(__name__, template_folder='templates')
app.secret_key = 'food-hub-secret-2026'

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'food_hub.db')

# ──────────────────────────────────────────────
# Food Database (with nutrition & metadata)
# ──────────────────────────────────────────────

FOOD_DB = [
    {"id": 1,  "name": "Pizza",           "emoji": "🍕", "diet": ["any", "vegetarian"],                              "weather": ["rainy", "cold"],          "mood": ["sad", "happy"],  "time": ["night", "morning"], "desc": "A comforting slice of joy.",            "calories": 285, "protein": 12, "carbs": 36, "fat": 10, "category": "comfort",    "spice": "mild",   "prep_time": 25, "allergens": ["gluten", "dairy"]},
    {"id": 2,  "name": "Chocolate",       "emoji": "🍫", "diet": ["any", "vegetarian", "gluten-free"],               "weather": ["rainy", "cold"],          "mood": ["sad"],           "time": ["morning", "night"], "desc": "Sweet treat to boost your mood!",       "calories": 546, "protein": 5,  "carbs": 60, "fat": 31, "category": "dessert",    "spice": "none",   "prep_time": 0,  "allergens": ["dairy", "soy"]},
    {"id": 3,  "name": "Coffee",          "emoji": "☕",  "diet": ["any", "vegan", "vegetarian", "gluten-free"],      "weather": ["rainy", "cold"],          "mood": ["sad", "happy"],  "time": ["morning"],          "desc": "Warm up and energize.",                 "calories": 2,   "protein": 0,  "carbs": 0,  "fat": 0,  "category": "beverage",   "spice": "none",   "prep_time": 5,  "allergens": []},
    {"id": 4,  "name": "Ice Cream",       "emoji": "🍦", "diet": ["any", "vegetarian", "gluten-free"],               "weather": ["sunny"],                  "mood": ["happy"],         "time": ["morning", "night"], "desc": "Cool and refreshing!",                  "calories": 207, "protein": 4,  "carbs": 24, "fat": 11, "category": "dessert",    "spice": "none",   "prep_time": 0,  "allergens": ["dairy"]},
    {"id": 5,  "name": "Smoothie",        "emoji": "🍹", "diet": ["any", "vegan", "vegetarian", "gluten-free"],      "weather": ["sunny"],                  "mood": ["happy"],         "time": ["morning"],          "desc": "Vibrant, healthy, and fresh.",          "calories": 150, "protein": 3,  "carbs": 33, "fat": 1,  "category": "beverage",   "spice": "none",   "prep_time": 5,  "allergens": []},
    {"id": 6,  "name": "Sandwich",        "emoji": "🥪", "diet": ["any", "vegetarian"],                              "weather": ["sunny", "rainy"],         "mood": ["happy", "sad"],  "time": ["morning", "night"], "desc": "Quick and satisfying.",                 "calories": 350, "protein": 15, "carbs": 40, "fat": 14, "category": "quick-bite", "spice": "mild",   "prep_time": 10, "allergens": ["gluten", "dairy"]},
    {"id": 7,  "name": "Hot Soup",        "emoji": "🥣", "diet": ["any", "vegan", "vegetarian", "gluten-free"],      "weather": ["cold", "rainy"],          "mood": ["sad", "happy"],  "time": ["night", "morning"], "desc": "Like a warm hug in a bowl.",            "calories": 120, "protein": 6,  "carbs": 18, "fat": 3,  "category": "comfort",    "spice": "mild",   "prep_time": 30, "allergens": []},
    {"id": 8,  "name": "Maggi / Noodles", "emoji": "🍜", "diet": ["any", "vegetarian", "vegan"],                     "weather": ["cold", "rainy"],          "mood": ["happy", "sad"],  "time": ["night"],            "desc": "The ultimate late-night comfort.",      "calories": 205, "protein": 5,  "carbs": 28, "fat": 8,  "category": "comfort",    "spice": "medium", "prep_time": 5,  "allergens": ["gluten"]},
    {"id": 9,  "name": "Fruit Bowl",      "emoji": "🥗", "diet": ["any", "vegan", "vegetarian", "gluten-free"],      "weather": ["sunny", "cold"],          "mood": ["happy"],         "time": ["morning"],          "desc": "Light, fresh, and nutritious.",         "calories": 85,  "protein": 1,  "carbs": 21, "fat": 0,  "category": "healthy",    "spice": "none",   "prep_time": 5,  "allergens": []},
    {"id": 10, "name": "Burger",          "emoji": "🍔", "diet": ["any"],                                            "weather": ["sunny", "cold"],          "mood": ["happy"],         "time": ["night", "morning"], "desc": "Hearty and delicious.",                 "calories": 354, "protein": 20, "carbs": 29, "fat": 17, "category": "comfort",    "spice": "mild",   "prep_time": 15, "allergens": ["gluten", "dairy"]},
    {"id": 11, "name": "Pasta",           "emoji": "🍝", "diet": ["any", "vegetarian"],                              "weather": ["rainy", "cold"],          "mood": ["happy", "sad"],  "time": ["night"],            "desc": "Rich and filling Italian classic.",     "calories": 220, "protein": 8,  "carbs": 43, "fat": 1,  "category": "comfort",    "spice": "mild",   "prep_time": 20, "allergens": ["gluten"]},
    {"id": 12, "name": "Sushi",           "emoji": "🍣", "diet": ["any", "pescatarian", "gluten-free"],              "weather": ["sunny", "rainy"],         "mood": ["happy"],         "time": ["night"],            "desc": "Fresh flavors from the sea.",           "calories": 200, "protein": 9,  "carbs": 38, "fat": 1,  "category": "gourmet",    "spice": "mild",   "prep_time": 40, "allergens": ["shellfish", "soy"]},
    {"id": 13, "name": "Tacos",           "emoji": "🌮", "diet": ["any"],                                            "weather": ["sunny"],                  "mood": ["happy"],         "time": ["night"],            "desc": "Spicy and fun to eat!",                "calories": 226, "protein": 9,  "carbs": 20, "fat": 12, "category": "comfort",    "spice": "hot",    "prep_time": 15, "allergens": ["gluten", "dairy"]},
    {"id": 14, "name": "Pancakes",        "emoji": "🥞", "diet": ["any", "vegetarian"],                              "weather": ["sunny", "rainy"],         "mood": ["happy", "sad"],  "time": ["morning"],          "desc": "Fluffy stacks of perfection!",         "calories": 227, "protein": 6,  "carbs": 28, "fat": 10, "category": "breakfast",  "spice": "none",   "prep_time": 15, "allergens": ["gluten", "dairy", "eggs"]},
    {"id": 15, "name": "Chai / Tea",      "emoji": "🍵", "diet": ["any", "vegan", "vegetarian", "gluten-free"],      "weather": ["cold", "rainy"],          "mood": ["sad", "happy"],  "time": ["morning", "night"], "desc": "A soothing cup of warmth.",             "calories": 30,  "protein": 1,  "carbs": 5,  "fat": 1,  "category": "beverage",   "spice": "mild",   "prep_time": 5,  "allergens": ["dairy"]},
    {"id": 16, "name": "Biryani",         "emoji": "🍚", "diet": ["any"],                                            "weather": ["cold", "rainy"],          "mood": ["happy"],         "time": ["night"],            "desc": "Aromatic rice dish to celebrate.",      "calories": 350, "protein": 18, "carbs": 45, "fat": 12, "category": "gourmet",    "spice": "hot",    "prep_time": 45, "allergens": ["nuts"]},
    {"id": 17, "name": "Salad",           "emoji": "🥬", "diet": ["any", "vegan", "vegetarian", "gluten-free"],      "weather": ["sunny"],                  "mood": ["happy"],         "time": ["morning"],          "desc": "Light, crunchy, and guilt-free.",       "calories": 65,  "protein": 3,  "carbs": 12, "fat": 1,  "category": "healthy",    "spice": "none",   "prep_time": 10, "allergens": []},
    {"id": 18, "name": "Dosa",            "emoji": "🫓", "diet": ["any", "vegan", "vegetarian", "gluten-free"],      "weather": ["sunny", "rainy"],         "mood": ["happy"],         "time": ["morning"],          "desc": "Crispy South Indian delight.",          "calories": 168, "protein": 4,  "carbs": 28, "fat": 4,  "category": "breakfast",  "spice": "mild",   "prep_time": 20, "allergens": []},
    {"id": 19, "name": "Fries",           "emoji": "🍟", "diet": ["any", "vegan", "vegetarian", "gluten-free"],      "weather": ["sunny", "cold"],          "mood": ["happy", "sad"],  "time": ["night"],            "desc": "Crispy, salty, and addictive.",         "calories": 312, "protein": 4,  "carbs": 41, "fat": 15, "category": "quick-bite", "spice": "none",   "prep_time": 10, "allergens": []},
    {"id": 20, "name": "Doughnut",        "emoji": "🍩", "diet": ["any", "vegetarian"],                              "weather": ["sunny", "rainy"],         "mood": ["sad", "happy"],  "time": ["morning"],          "desc": "Sweet glazed happiness.",               "calories": 253, "protein": 3,  "carbs": 31, "fat": 14, "category": "dessert",    "spice": "none",   "prep_time": 0,  "allergens": ["gluten", "dairy", "eggs"]},
]

FOOD_BY_ID = {f["id"]: f for f in FOOD_DB}

# ──────────────────────────────────────────────
# Database Setup
# ──────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            avatar_emoji TEXT DEFAULT '😊',
            default_diet TEXT DEFAULT 'any',
            allergies TEXT DEFAULT '',
            spice_preference TEXT DEFAULT 'any',
            calorie_goal INTEGER DEFAULT 2000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mood TEXT,
            weather TEXT,
            time_of_day TEXT,
            diet TEXT,
            recommended_ids TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            food_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, food_id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hash password with SHA-256 + salt for basic security."""
    salt = 'foodhub_salt_2026'
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def get_current_user_id():
    """Get the logged-in user's ID from session, or None."""
    return session.get('user_id')

def require_auth(f):
    """Decorator to require authentication for API endpoints."""
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not get_current_user_id():
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)
    return decorated

# ──────────────────────────────────────────────
# Auth API
# ──────────────────────────────────────────────

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    data = request.get_json() or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')
    display_name = data.get('display_name', '').strip()

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if len(username) < 3:
        return jsonify({"error": "Username must be at least 3 characters"}), 400
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters"}), 400
    if not display_name:
        display_name = username.capitalize()

    conn = get_db()
    existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "Username already taken"}), 409

    password_hash = hash_password(password)
    cursor = conn.execute(
        'INSERT INTO users (username, password_hash, display_name) VALUES (?, ?, ?)',
        (username, password_hash, display_name)
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    session['user_id'] = user_id
    return jsonify({
        "message": "Account created!",
        "user": {"id": user_id, "username": username, "display_name": display_name, "avatar_emoji": "😊"}
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip().lower()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if not user or user['password_hash'] != hash_password(password):
        return jsonify({"error": "Invalid username or password"}), 401

    session['user_id'] = user['id']
    return jsonify({
        "message": f"Welcome back, {user['display_name']}!",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "display_name": user['display_name'],
            "avatar_emoji": user['avatar_emoji'],
            "default_diet": user['default_diet'],
            "allergies": user['allergies'],
            "spice_preference": user['spice_preference'],
            "calorie_goal": user['calorie_goal'],
        }
    })

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route('/api/auth/me', methods=['GET'])
def api_me():
    user_id = get_current_user_id()
    if not user_id:
        return jsonify({"authenticated": False})

    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    if not user:
        session.clear()
        return jsonify({"authenticated": False})

    return jsonify({
        "authenticated": True,
        "user": {
            "id": user['id'],
            "username": user['username'],
            "display_name": user['display_name'],
            "avatar_emoji": user['avatar_emoji'],
            "default_diet": user['default_diet'],
            "allergies": user['allergies'],
            "spice_preference": user['spice_preference'],
            "calorie_goal": user['calorie_goal'],
            "created_at": user['created_at'],
        }
    })

# ──────────────────────────────────────────────
# Profile API
# ──────────────────────────────────────────────

@app.route('/api/profile', methods=['PUT'])
@require_auth
def api_update_profile():
    user_id = get_current_user_id()
    data = request.get_json() or {}

    allowed_fields = {
        'display_name': str,
        'avatar_emoji': str,
        'default_diet': str,
        'allergies': str,
        'spice_preference': str,
        'calorie_goal': int,
    }

    updates = []
    values = []
    for field, field_type in allowed_fields.items():
        if field in data:
            val = data[field]
            if field_type == int:
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    continue
            else:
                val = str(val).strip()
            updates.append(f"{field} = ?")
            values.append(val)

    if not updates:
        return jsonify({"error": "No valid fields to update"}), 400

    values.append(user_id)
    conn = get_db()
    conn.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', values)
    conn.commit()

    # Return updated user
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    return jsonify({
        "message": "Profile updated!",
        "user": {
            "id": user['id'],
            "username": user['username'],
            "display_name": user['display_name'],
            "avatar_emoji": user['avatar_emoji'],
            "default_diet": user['default_diet'],
            "allergies": user['allergies'],
            "spice_preference": user['spice_preference'],
            "calorie_goal": user['calorie_goal'],
        }
    })

@app.route('/api/profile/password', methods=['PUT'])
@require_auth
def api_change_password():
    user_id = get_current_user_id()
    data = request.get_json() or {}
    current = data.get('current_password', '')
    new_pass = data.get('new_password', '')

    if not current or not new_pass:
        return jsonify({"error": "Both current and new password are required"}), 400
    if len(new_pass) < 4:
        return jsonify({"error": "New password must be at least 4 characters"}), 400

    conn = get_db()
    user = conn.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,)).fetchone()
    if user['password_hash'] != hash_password(current):
        conn.close()
        return jsonify({"error": "Current password is incorrect"}), 403

    conn.execute('UPDATE users SET password_hash = ? WHERE id = ?', (hash_password(new_pass), user_id))
    conn.commit()
    conn.close()
    return jsonify({"message": "Password changed successfully!"})

# ──────────────────────────────────────────────
# Smart Recommendation Engine
# ──────────────────────────────────────────────

def get_user_profile(user_id):
    """Get user profile for personalization."""
    conn = get_db()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return dict(user)
    return None

def get_user_favorite_ids(user_id):
    conn = get_db()
    rows = conn.execute('SELECT food_id FROM favorites WHERE user_id = ?', (user_id,)).fetchall()
    conn.close()
    return [r['food_id'] for r in rows]

def get_recent_recommendation_ids(user_id, limit=5):
    """Get food IDs from recent recommendations to encourage variety."""
    conn = get_db()
    rows = conn.execute(
        'SELECT recommended_ids FROM history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?',
        (user_id, limit)
    ).fetchall()
    conn.close()
    recent_ids = []
    for r in rows:
        try:
            recent_ids.extend(json.loads(r['recommended_ids']))
        except (json.JSONDecodeError, TypeError):
            pass
    return recent_ids

def recommend_food(mood, weather, time_of_day, diet, user_id):
    """
    Smart recommendation engine:
    - Base score from mood/weather/time match (0-3)
    - Bonus for foods in same category as favorites (+0.5)
    - Penalty for recently recommended foods (-1) for variety
    - Filters out foods with user's allergens
    - Respects spice preference from profile
    """
    fav_ids = get_user_favorite_ids(user_id)
    recent_ids = get_recent_recommendation_ids(user_id)
    profile = get_user_profile(user_id)

    # Parse user allergies from profile
    user_allergies = set()
    if profile and profile.get('allergies'):
        user_allergies = {a.strip().lower() for a in profile['allergies'].split(',') if a.strip()}

    # Get spice preference from profile
    spice_pref = (profile.get('spice_preference', 'any') if profile else 'any')

    # Get favorite categories for boosting similar foods
    fav_categories = set()
    for fid in fav_ids:
        if fid in FOOD_BY_ID:
            fav_categories.add(FOOD_BY_ID[fid]["category"])

    available = []
    for f in FOOD_DB:
        # Diet filter
        if diet != "any" and diet not in f.get("diet", []):
            continue

        # Allergy filter: skip foods containing user's allergens
        food_allergens = {a.lower() for a in f.get("allergens", [])}
        if user_allergies & food_allergens:
            continue

        food = dict(f)

        # Base score: mood + weather + time match
        score = 0.0
        if mood in f.get("mood", []):
            score += 1
        if weather in f.get("weather", []):
            score += 1
        if time_of_day in f.get("time", []):
            score += 1

        # Personalization: boost foods similar to favorites
        if f["category"] in fav_categories:
            score += 0.5

        # Personalization: direct favorites get a small boost
        if f["id"] in fav_ids:
            score += 0.3

        # Spice preference scoring
        if spice_pref != 'any':
            spice_map = {'none': 0, 'mild': 1, 'medium': 2, 'hot': 3}
            user_spice = spice_map.get(spice_pref, 1)
            food_spice = spice_map.get(f.get('spice', 'mild'), 1)
            if abs(user_spice - food_spice) <= 1:
                score += 0.3  # Close to preference
            elif abs(user_spice - food_spice) >= 2:
                score -= 0.3  # Far from preference

        # Variety: penalize recently recommended foods
        recent_count = recent_ids.count(f["id"])
        if recent_count > 0:
            score -= 0.4 * recent_count

        food["score"] = round(score, 1)
        food["is_favorite"] = f["id"] in fav_ids
        available.append(food)

    available.sort(key=lambda x: x["score"], reverse=True)
    return available[:5]

# ──────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────

@app.route('/')
def home():
    return render_template("index.html")

# ──────────────────────────────────────────────
# API: Recommendations
# ──────────────────────────────────────────────

@app.route('/api/recommend', methods=['POST'])
@require_auth
def api_recommend():
    data = request.get_json() or {}
    mood = data.get('mood', 'happy')
    weather = data.get('weather', 'sunny')
    time_of_day = data.get('time', 'morning')
    diet = data.get('diet', 'any')
    user_id = get_current_user_id()

    foods = recommend_food(mood, weather, time_of_day, diet, user_id)

    # Save to history
    rec_ids = [f["id"] for f in foods]
    conn = get_db()
    conn.execute(
        'INSERT INTO history (user_id, mood, weather, time_of_day, diet, recommended_ids) VALUES (?, ?, ?, ?, ?, ?)',
        (user_id, mood, weather, time_of_day, diet, json.dumps(rec_ids))
    )
    conn.commit()
    conn.close()

    return jsonify({"foods": foods})

# ──────────────────────────────────────────────
# API: Favorites
# ──────────────────────────────────────────────

@app.route('/api/favorites', methods=['GET'])
@require_auth
def api_get_favorites():
    user_id = get_current_user_id()
    fav_ids = get_user_favorite_ids(user_id)
    foods = []
    for fid in fav_ids:
        if fid in FOOD_BY_ID:
            food = dict(FOOD_BY_ID[fid])
            food["is_favorite"] = True
            foods.append(food)
    return jsonify({"favorites": foods})

@app.route('/api/favorites/<int:food_id>', methods=['POST'])
@require_auth
def api_toggle_favorite(food_id):
    user_id = get_current_user_id()
    if food_id not in FOOD_BY_ID:
        return jsonify({"error": "Food not found"}), 404

    conn = get_db()
    existing = conn.execute(
        'SELECT id FROM favorites WHERE user_id = ? AND food_id = ?',
        (user_id, food_id)
    ).fetchone()

    if existing:
        conn.execute('DELETE FROM favorites WHERE user_id = ? AND food_id = ?', (user_id, food_id))
        conn.commit()
        conn.close()
        return jsonify({"action": "removed", "food_id": food_id})
    else:
        conn.execute(
            'INSERT INTO favorites (user_id, food_id) VALUES (?, ?)',
            (user_id, food_id)
        )
        conn.commit()
        conn.close()
        return jsonify({"action": "added", "food_id": food_id})

# ──────────────────────────────────────────────
# API: History
# ──────────────────────────────────────────────

@app.route('/api/history', methods=['GET'])
@require_auth
def api_history():
    user_id = get_current_user_id()
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC LIMIT 20',
        (user_id,)
    ).fetchall()
    conn.close()

    history = []
    for r in rows:
        food_ids = json.loads(r['recommended_ids']) if r['recommended_ids'] else []
        food_names = []
        for fid in food_ids:
            if fid in FOOD_BY_ID:
                food_names.append({
                    "id": fid,
                    "name": FOOD_BY_ID[fid]["name"],
                    "emoji": FOOD_BY_ID[fid]["emoji"]
                })
        history.append({
            "id": r['id'],
            "mood": r['mood'],
            "weather": r['weather'],
            "time": r['time_of_day'],
            "diet": r['diet'],
            "foods": food_names,
            "created_at": r['created_at']
        })

    return jsonify({"history": history})

@app.route('/api/history', methods=['DELETE'])
@require_auth
def api_clear_history():
    user_id = get_current_user_id()
    conn = get_db()
    conn.execute('DELETE FROM history WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({"status": "cleared"})

# ──────────────────────────────────────────────
# API: Insights / Food Personality
# ──────────────────────────────────────────────

PERSONALITY_MAP = {
    ("comfort", "sad"):     {"title": "The Comfort Seeker",     "emoji": "🧸", "desc": "You turn to food for warmth and comfort. Your plate is a cozy blanket."},
    ("comfort", "happy"):   {"title": "The Joy Feaster",        "emoji": "🎉", "desc": "You celebrate life with hearty, feel-good meals."},
    ("healthy", "happy"):   {"title": "The Wellness Warrior",   "emoji": "💪", "desc": "You fuel your body with clean, nutritious choices."},
    ("dessert", "sad"):     {"title": "The Sweet Escapist",     "emoji": "🍰", "desc": "Sugar is your therapy. No judgment — we all need a little sweetness."},
    ("dessert", "happy"):   {"title": "The Sweet Tooth",        "emoji": "🍬", "desc": "Life is short, eat dessert first! You live for the sweet things."},
    ("beverage", "sad"):    {"title": "The Sipper",             "emoji": "☕", "desc": "A warm drink fixes everything. You find peace in every cup."},
    ("beverage", "happy"):  {"title": "The Chill Vibes",        "emoji": "🧃", "desc": "You keep it simple and refreshing."},
    ("gourmet", "happy"):   {"title": "The Foodie Explorer",    "emoji": "🌍", "desc": "You seek bold, exotic flavors and love culinary adventures."},
    ("quick-bite", "happy"):{"title": "The On-The-Go Snacker",  "emoji": "⚡", "desc": "Fast, satisfying, and always ready — that's your food style."},
    ("breakfast", "happy"): {"title": "The Morning Person",     "emoji": "🌅", "desc": "Breakfast is your love language. You start every day right."},
}

@app.route('/api/insights', methods=['GET'])
@require_auth
def api_insights():
    user_id = get_current_user_id()
    conn = get_db()
    rows = conn.execute(
        'SELECT * FROM history WHERE user_id = ? ORDER BY created_at DESC',
        (user_id,)
    ).fetchall()
    fav_rows = conn.execute(
        'SELECT food_id FROM favorites WHERE user_id = ?', (user_id,)
    ).fetchall()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    if not rows:
        return jsonify({
            "total_recommendations": 0,
            "total_favorites": len(fav_rows),
            "personality": {"title": "The Newcomer", "emoji": "🌟", "desc": "Get some recommendations to discover your food personality!"},
            "top_mood": None,
            "top_weather": None,
            "top_category": None,
            "top_foods": [],
            "avg_calories": 0,
            "member_since": user['created_at'] if user else None,
        })

    moods = [r['mood'] for r in rows]
    weathers = [r['weather'] for r in rows]

    # Find most recommended foods
    all_food_ids = []
    for r in rows:
        try:
            all_food_ids.extend(json.loads(r['recommended_ids']))
        except (json.JSONDecodeError, TypeError):
            pass

    food_counter = Counter(all_food_ids)
    top_food_ids = [fid for fid, _ in food_counter.most_common(5)]
    top_foods = []
    for fid in top_food_ids:
        if fid in FOOD_BY_ID:
            top_foods.append({
                "name": FOOD_BY_ID[fid]["name"],
                "emoji": FOOD_BY_ID[fid]["emoji"],
                "count": food_counter[fid]
            })

    # Determine personality
    top_mood = Counter(moods).most_common(1)[0][0] if moods else "happy"
    top_categories = []
    for fid in all_food_ids:
        if fid in FOOD_BY_ID:
            top_categories.append(FOOD_BY_ID[fid]["category"])
    top_category = Counter(top_categories).most_common(1)[0][0] if top_categories else "comfort"

    personality = PERSONALITY_MAP.get(
        (top_category, top_mood),
        {"title": "The Eclectic Eater", "emoji": "🎭", "desc": "You have diverse taste! Your plate is a canvas of variety."}
    )

    # Avg calories
    cal_list = [FOOD_BY_ID[fid]["calories"] for fid in all_food_ids if fid in FOOD_BY_ID]
    avg_cal = round(sum(cal_list) / len(cal_list)) if cal_list else 0

    return jsonify({
        "total_recommendations": len(rows),
        "total_favorites": len(fav_rows),
        "personality": personality,
        "top_mood": Counter(moods).most_common(1)[0][0] if moods else None,
        "top_weather": Counter(weathers).most_common(1)[0][0] if weathers else None,
        "top_category": top_category,
        "top_foods": top_foods,
        "avg_calories": avg_cal,
        "member_since": user['created_at'] if user else None,
    })

# ──────────────────────────────────────────────
# API: Recipe Search (TheMealDB — free, no key)
# ──────────────────────────────────────────────

@app.route('/api/search', methods=['GET'])
def api_search_recipes():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({"recipes": []})

    try:
        url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'FoodHub/1.0'})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return jsonify({"recipes": [], "error": "Could not reach recipe API"})

    meals = data.get("meals") or []
    recipes = []
    for meal in meals[:8]:
        ingredients = []
        for i in range(1, 21):
            ing = meal.get(f"strIngredient{i}", "")
            measure = meal.get(f"strMeasure{i}", "")
            if ing and ing.strip():
                ingredients.append(f"{measure.strip()} {ing.strip()}".strip())

        recipes.append({
            "id": meal.get("idMeal"),
            "name": meal.get("strMeal", ""),
            "category": meal.get("strCategory", ""),
            "area": meal.get("strArea", ""),
            "instructions": meal.get("strInstructions", ""),
            "image": meal.get("strMealThumb", ""),
            "video": meal.get("strYoutube", ""),
            "ingredients": ingredients,
        })

    return jsonify({"recipes": recipes})

# ──────────────────────────────────────────────
# API: All Foods
# ──────────────────────────────────────────────

@app.route('/api/foods', methods=['GET'])
def api_all_foods():
    user_id = get_current_user_id()
    fav_ids = get_user_favorite_ids(user_id) if user_id else []
    foods = []
    for f in FOOD_DB:
        food = dict(f)
        food["is_favorite"] = f["id"] in fav_ids
        foods.append(food)
    return jsonify({"foods": foods})

# ──────────────────────────────────────────────
# Initialize & Run
# ──────────────────────────────────────────────

init_db()

if __name__ == "__main__":
    app.run(debug=True)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)