from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from googletrans import Translator
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fallback-dev-key")

# ── MongoDB connection ─────────────────────────────────────────────
client = MongoClient(os.environ.get("MONGO_URI"))
db     = client["speech_to_sign"]
users  = db["users"]

IMAGE_FOLDER = "static/hand_signs/"

# ── Auth guard decorator ───────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

# ── Routes ─────────────────────────────────────────────────────────

@app.route("/")
@login_required
def index():
    return render_template("index.html",
                           user_name=session.get("user_name"),
                           user_email=session.get("user_email"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if "user_id" in session:
        return redirect(url_for("index"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Basic validation
        if not name or not email or not password:
            return render_template("signup.html",
                                   error="All fields are required.",
                                   name=name, email=email)

        if len(password) < 6:
            return render_template("signup.html",
                                   error="Password must be at least 6 characters.",
                                   name=name, email=email)

        if users.find_one({"email": email}):
            return render_template("signup.html",
                                   error="Email already registered. Please log in.",
                                   name=name)

        # Store with hashed password
        users.insert_one({
            "name":       name,
            "email":      email,
            "password":   generate_password_hash(password),
            "created_at": datetime.utcnow()
        })

        return redirect(url_for("login", success="1"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("index"))

    success = request.args.get("success")

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = users.find_one({"email": email})

        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html",
                                   error="Invalid email or password.")

        session["user_id"]    = str(user["_id"])
        session["user_name"]  = user["name"]
        session["user_email"] = user["email"]

        return redirect(url_for("index"))

    return render_template("login.html", success=success)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/recognize_speech", methods=["POST"])
@login_required
def recognize_speech():
    try:
        data = request.get_json()
        text = data.get("text")
        lang = data.get("lang")

        if not text:
            return jsonify({"error": "No text provided!"}), 400

        if lang in ['hi', 'mr']:
            translator    = Translator()
            translated_text = translator.translate(text, src=lang, dest='en').text
        else:
            translated_text = text

        images = []
        for letter in translated_text.upper():
            if letter == " ":
                images.append("__SPACE__")
            elif letter.isalpha():
                image_path = os.path.join(IMAGE_FOLDER, f"{letter}.png")
                if os.path.exists(image_path):
                    images.append(f"/{image_path}")
                else:
                    images.append(f"/static/hand_signs/missing.png")

        return jsonify({"text": text, "translated_text": translated_text, "images": images})

    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
