"""Flask app for MoviWebApp with validation, docstrings, and rating display."""

import os
from pathlib import Path
from typing import Optional

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from models import db
from data_manager import DataManager
from models import User, Movie

# -------------------- App config --------------------

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

# ensure ./data exists and DB path is absolute
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "moviweb.sqlite"

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

dm = DataManager()


# -------------------- Error handlers --------------------

@app.errorhandler(404)
def not_found(_e):
    """Render a friendly 404 page."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_error(_e):
    """Render a friendly 500 page."""
    return render_template("500.html"), 500


# -------------------- Routes --------------------

@app.route("/")
def index():
    """Homepage: list users and show create-user form."""
    users = dm.get_users()
    return render_template("index.html", users=users)


@app.route("/users", methods=["POST"])
def create_user():
    """Create a new user from form data; redirects back to index."""
    name = request.form.get("name", "")
    _user, err = dm.create_user(name)
    if err:
        flash(err, "error")
    else:
        flash("User created successfully.", "success")
    return redirect(url_for("index"))


@app.route("/users/<int:user_id>/movies", methods=["GET"])
def list_movies(user_id: int):
    """Show a user's movies with rating display and forms to update/delete."""
    user = dm.get_user(user_id)
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("index"))

    movies = dm.get_movies(user_id)
    return render_template("movies.html", user=user, movies=movies)


@app.route("/users/<int:user_id>/movies", methods=["POST"])
def add_movie(user_id: int):
    """Add a movie for user from form input."""
    title = request.form.get("title", "")
    year = request.form.get("year") or None
    poster = request.form.get("poster_url") or None
    rating_raw = request.form.get("rating") or None

    rating: Optional[int] = None
    if rating_raw not in (None, "", "None"):
        rating = rating_raw  # DataManager coerces/validates

    _movie, err = dm.add_movie(user_id, title=title, year=year, poster_url=poster, rating=rating)
    if err:
        flash(err, "error")
    else:
        flash("Movie added.", "success")
    return redirect(url_for("list_movies", user_id=user_id))


@app.route("/users/<int:user_id>/movies/<int:movie_id>/update", methods=["POST"])
def update_movie(user_id: int, movie_id: int):
    """Update a movie (title/rating/year/poster)."""
    new_title = request.form.get("title")
    new_rating = request.form.get("rating")
    new_year = request.form.get("year")
    new_poster = request.form.get("poster_url")

    err = dm.update_movie(
        movie_id,
        title=new_title,
        rating=new_rating if new_rating not in ("", None) else None,
        year=new_year if new_year not in ("", None) else None,
        poster_url=new_poster if new_poster not in ("", None) else None,
    )
    if err:
        flash(err, "error")
    else:
        flash("Movie updated.", "success")
    return redirect(url_for("list_movies", user_id=user_id))


@app.route("/users/<int:user_id>/movies/<int:movie_id>/delete", methods=["POST"])
def delete_movie(user_id: int, movie_id: int):
    """Delete a movie."""
    err = dm.delete_movie(movie_id)
    if err:
        flash(err, "error")
    else:
        flash("Movie deleted.", "success")
    return redirect(url_for("list_movies", user_id=user_id))


if __name__ == "__main__":
    # Choose a free port if 5000 busy; adjust as you like
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)