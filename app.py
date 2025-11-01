import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from models import db, User, Movie
from data_manager import DataManager

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret")

# SQLite DB path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "moviweb.sqlite")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

data_manager = DataManager()


# ----------------- USERS -----------------
@app.route("/")
def index():
    users = data_manager.get_users()
    return render_template("index.html", users=users)


@app.route("/users", methods=["POST"])
def create_user():
    name = (request.form.get("name") or "").strip()
    if not name:
        flash("Name is required.", "error")
        return redirect(url_for("index"))

    try:
        data_manager.create_user(name)
        flash(f"User '{name}' created.", "success")
    except Exception as e:
        flash(f"Could not create user: {e}", "error")

    return redirect(url_for("index"))


# ----------------- MOVIES -----------------
@app.route("/users/<int:user_id>/movies", methods=["GET"])
def list_movies(user_id):
    user = User.query.get_or_404(user_id)
    movies = data_manager.get_movies(user_id)
    return render_template("movies.html", user=user, movies=movies)


@app.route("/users/<int:user_id>/movies", methods=["POST"])
def add_movie(user_id):
    """
    Add a movie for this user. Minimal form: title (required), optional year & poster_url.
    If you want OMDb fetch here, you can do it and pass year/poster_url from that response.
    """
    title = (request.form.get("title") or "").strip()
    year = (request.form.get("year") or "").strip() or None
    poster_url = (request.form.get("poster_url") or "").strip() or None

    if not title:
        flash("Movie title is required.", "error")
        return redirect(url_for("list_movies", user_id=user_id))

    try:
        data_manager.add_movie(user_id, title, year=year, poster_url=poster_url)
        flash(f"Added '{title}'.", "success")
    except LookupError:
        abort(404)
    except Exception as e:
        flash(f"Could not add movie: {e}", "error")

    return redirect(url_for("list_movies", user_id=user_id))


@app.route("/users/<int:user_id>/movies/<int:movie_id>/update", methods=["POST"])
def update_movie(user_id, movie_id):
    """Update title/year/poster for a specific movie."""
    new_title = (request.form.get("title") or "").strip() or None
    new_year = (request.form.get("year") or "").strip() or None
    new_poster = (request.form.get("poster_url") or "").strip() or None

    try:
        data_manager.update_movie(movie_id, new_title, new_year, new_poster)
        flash("Movie updated.", "success")
    except LookupError:
        abort(404)
    except Exception as e:
        flash(f"Could not update movie: {e}", "error")

    return redirect(url_for("list_movies", user_id=user_id))


@app.route("/users/<int:user_id>/movies/<int:movie_id>/delete", methods=["POST"])
def delete_movie(user_id, movie_id):
    try:
        data_manager.delete_movie(movie_id)
        flash("Movie deleted.", "success")
    except LookupError:
        abort(404)
    except Exception as e:
        flash(f"Could not delete movie: {e}", "error")

    return redirect(url_for("list_movies", user_id=user_id))

# ----------------- ERROR HANDLERS -----------------

@app.errorhandler(404)
def page_not_found(e):
    """Render a friendly 404 error page."""
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    """Handle unexpected server errors gracefully."""
    return (
        render_template("500.html", error_message=str(e)),
        500,
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)