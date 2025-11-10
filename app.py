# app.py
from __future__ import annotations
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_cors import CORS

from models import db, User, Movie
from data_manager import DataManager

# --- Env / App setup ---
load_dotenv()

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")  # for flash messages
CORS(app)

# Ensure data dir exists
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# SQLite file
DB_PATH = DATA_DIR / "moviweb.sqlite"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Init DB
db.init_app(app)
data_manager = DataManager()

# ---------- Error Handlers ----------

@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Resource not found."), 404

@app.errorhandler(400)
def bad_request(e):
    return render_template("error.html", code=400, message="Bad request."), 400

@app.errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Internal server error."), 500


# ---------- Routes ----------

@app.route("/")
def index():
    """
    Home page: list users and provide a form to create a new user.
    """
    users = data_manager.get_users()
    return render_template("index.html", users=users)

@app.route("/users", methods=["POST"])
def create_user():
    """
    Form POST to create a new user.
    """
    name = request.form.get("name", "")
    user, err = data_manager.create_user(name)
    if err:
        flash(err, "error")
    else:
        flash(f"User '{user.name}' created.", "success")
    return redirect(url_for("index"))

@app.route("/users/<int:user_id>/movies", methods=["GET"])
def list_movies(user_id: int):
    """
    Shows all movies for a given user and the add-movie form.
    """
    user = User.query.get_or_404(user_id)
    movies = data_manager.get_movies(user_id)
    return render_template("movies.html", user=user, movies=movies)

@app.route("/users/<int:user_id>/movies", methods=["POST"])
def add_movie(user_id: int):
    """
    Adds a movie for the user (with OMDb enrichment).
    """
    # title input can be 'title', rating from 'rating'
    title = request.form.get("title", "")
    rating = request.form.get("rating", "")

    movie, err = data_manager.add_movie(user_id, title, rating)
    if err:
        flash(err, "error")
    else:
        flash(f"Movie '{movie.title}' added.", "success")
    return redirect(url_for("list_movies", user_id=user_id))

@app.route("/users/<int:user_id>/movies/<int:movie_id>/update", methods=["POST"])
def update_movie(user_id: int, movie_id: int):
    """
    Updates title/rating for a movie.
    """
    title = request.form.get("title")  # optional
    rating = request.form.get("rating")  # optional
    movie, err = data_manager.update_movie(movie_id, title, rating)
    if err:
        flash(err, "error")
    else:
        flash(f"Movie '{movie.title}' updated.", "success")
    return redirect(url_for("list_movies", user_id=user_id))

@app.route("/users/<int:user_id>/movies/<int:movie_id>/delete", methods=["POST"])
def delete_movie(user_id: int, movie_id: int):
    """
    Deletes a movie for a user.
    """
    err = data_manager.delete_movie(movie_id)
    if err:
        flash(err, "error")
    else:
        flash("Movie deleted.", "success")
    return redirect(url_for("list_movies", user_id=user_id))


if __name__ == "__main__":
    # Create tables on first run
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=True)