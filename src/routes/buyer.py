"""Buyer-related routes"""

from flask import Blueprint, render_template, request, session, redirect
import json
from src.models import Profile, freelance_post
from src.utils.database import get_db
from src.utils.search_engine import SearchQuery
from src.config import SERVICE_TAGS

buyer_bp = Blueprint('buyer', __name__)

def recommend(posts):
    """Recommend posts based on user preferences"""
    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("SELECT preferences FROM users WHERE id = %s", (session["user_id"],))
        row = cursor.fetchone()
        preferences = json.loads(row["preferences"]) if row and row["preferences"] else []
    
    if not preferences:
        return posts
    
    engine = SearchQuery(posts)
    query = " ".join(preferences)
    results = engine.search(query)
    return [item for item, _ in results]

@buyer_bp.route("/buyer", methods=["GET"])
def buyer():
    user_id = session["user_id"]
    
    with get_db() as db:
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT services.id, services.title, services.description, services.price, 
                   services.image_url, users.resume, users.username
            FROM services
            JOIN users ON services.user_id = users.id
            WHERE services.user_id != %s
        """, (user_id,))
        services = cursor.fetchall()
        
        cursor.execute("SELECT preferences FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        user_preferences = json.loads(row["preferences"]) if row and row["preferences"] else []
    
    posts = [
        freelance_post(
            row["title"], row["description"], row["price"], row["id"], 
            row["resume"], row["username"], row["image_url"]
        ) 
        for row in services
    ]
    
    ranked_items = recommend(posts)
    active_category = user_preferences[0] if user_preferences else None
    
    reordered_tags = list(SERVICE_TAGS)
    if active_category and active_category in reordered_tags:
        reordered_tags.remove(active_category)
        reordered_tags.insert(0, active_category)

    session["profile_type"] = "buyer"
    user_profile = Profile(session["username"], "buyer", None, user_id, resume=session.get("resume", ""))
    
    return render_template(
        "mainpage_buyer.html", 
        items=ranked_items, 
        profile=user_profile, 
        tags=reordered_tags, 
        selected_category=active_category
    )

@buyer_bp.route("/set_preferences", methods=["POST"])
def set_preferences():
    selected_tags = request.form.get("selected_tags", "[]")
    
    try:
        preferences = json.loads(selected_tags)
    except:
        preferences = []

    preferences_str = json.dumps(preferences)

    with get_db() as db:
        cursor = db.cursor()
        cursor.execute("UPDATE users SET preferences = %s WHERE id = %s", (preferences_str, session["user_id"]))
    
    return redirect("/buyer")

@buyer_bp.route("/search", methods=["GET"])
def search():
    user_id = session["user_id"]
    query = request.args.get("query")
    
    with get_db() as db:
        cursor = db.cursor()
        
        cursor.execute("""
            SELECT services.id, services.title, services.description, services.price, 
                   services.image_url, users.resume, users.username 
            FROM services
            JOIN users ON services.user_id = users.id
            WHERE services.user_id != %s
        """, (user_id,))
        services = cursor.fetchall()
        
        cursor.execute("SELECT preferences FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        user_preferences = json.loads(row["preferences"]) if row and row["preferences"] else []
    
    posts = [
        freelance_post(
            row["title"], row["description"], row["price"], row["id"], 
            row["resume"], row["username"], row["image_url"]
        ) 
        for row in services
    ]
    
    if query:
        engine = SearchQuery(posts)
        results = engine.search(query)
        items_ranked = [item for item, _ in results]
    else:
        items_ranked = posts

    selected_category = user_preferences[0] if user_preferences else None
    user_profile = Profile(session["username"], session["profile_type"], None, user_id, resume=session.get("resume", ""))
    
    return render_template(
        "mainpage_buyer.html", 
        items=items_ranked, 
        profile=user_profile, 
        tags=SERVICE_TAGS, 
        selected_category=selected_category
    )