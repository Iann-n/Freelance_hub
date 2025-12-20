"""Authentication routes (login, register, logout)"""
from flask import Blueprint, render_template, request, session, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import Profile
from src.utils.database import get_db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/", methods=["GET"])
def index():
    return render_template("login.html")

@auth_bp.route("/home", methods=["GET"])
def home():
    if "user_id" not in session:
        return redirect("/")
    
    user_profile = Profile(
        session["username"], 
        session.get("profile_type", "buyer"), 
        session.get("password"), 
        session["user_id"], 
        resume=session.get("resume", "")
    )
    return render_template("home.html", profile=user_profile)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")
        password_confirm = request.form.get("confirmation")

        if not name:
            return render_template("error.html", error="Please enter name")
        if not password:
            return render_template("error.html", error="Please enter password")
        if not password_confirm:
            return render_template("error.html", error="Please confirm password")
        if password != password_confirm:
            return render_template("error.html", error="Passwords do not match")
        
        with get_db() as db:
            cursor = db.cursor()
            
            existing = cursor.execute("SELECT username FROM users WHERE username = %s", (name,)).fetchone()
            if existing:
                return render_template("error.html", error="Name is taken")
            
            hashed_password = generate_password_hash(password, method='pbkdf2:sha512')
            
            cursor.execute(
                "INSERT INTO users (username, password, is_buyer, is_seller) VALUES (%s, %s, %s, %s)", 
                (name, hashed_password, 1, 0)
            )
            
            user = cursor.execute("SELECT * FROM users WHERE username = %s", (name,)).fetchone()
            
            session["user_id"] = user["id"]
            session["username"] = name
            session["profile_type"] = "buyer"
            session["password"] = user["password"]
            session["resume"] = user["resume"] or ""

        return redirect("/home")
    
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        name = request.form.get("username")
        password = request.form.get("password")

        if not name:
            return render_template("error.html", error="Please enter name")
        if not password:
            return render_template("error.html", error="Please enter password")
        
        with get_db() as db:
            cursor = db.cursor()
            user = cursor.execute("SELECT * FROM users WHERE username = %s", (name,)).fetchone()

            if not user or not check_password_hash(user["password"], password):
                return render_template("error.html", error="Invalid username or password")

            session["user_id"] = user["id"]
            session["username"] = name
            session["password"] = user["password"]
            session["resume"] = user["resume"] or ""
            session["profile_type"] = "seller" if user["is_seller"] == 1 else "buyer"

        return redirect("/home")
    
    return render_template("login.html")