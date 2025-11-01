from typing import List, Optional
from models import db, User, Movie


class DataManager:
    """Encapsulates all DB CRUD ops for Users and Movies."""

    # ---------- Users ----------
    def create_user(self, name: str) -> User:
        name = (name or "").strip()
        if not name:
            raise ValueError("User name is required.")
        user = User(name=name)
        db.session.add(user)
        db.session.commit()
        return user

    def get_users(self) -> List[User]:
        return User.query.order_by(User.name.asc()).all()

    def get_user_or_404(self, user_id: int) -> User:
        user = User.query.get(user_id)
        if not user:
            raise LookupError("User not found")
        return user

    # ---------- Movies ----------
    def get_movies(self, user_id: int) -> List[Movie]:
        return Movie.query.filter_by(user_id=user_id).order_by(Movie.title.asc()).all()

    def add_movie(
        self,
        user_id: int,
        title: str,
        year: Optional[str] = None,
        poster_url: Optional[str] = None,
    ) -> Movie:
        title = (title or "").strip()
        if not title:
            raise ValueError("Movie title is required.")
        # ensure user exists
        self.get_user_or_404(user_id)

        movie = Movie(user_id=user_id, title=title, year=year, poster_url=poster_url)
        db.session.add(movie)
        db.session.commit()
        return movie

    def update_movie(
        self,
        movie_id: int,
        new_title: Optional[str] = None,
        new_year: Optional[str] = None,
        new_poster_url: Optional[str] = None,
    ) -> Movie:
        movie = Movie.query.get(movie_id)
        if not movie:
            raise LookupError("Movie not found")

        if new_title is not None and new_title.strip():
            movie.title = new_title.strip()
        if new_year is not None:
            movie.year = new_year.strip()
        if new_poster_url is not None:
            movie.poster_url = new_poster_url.strip()

        db.session.commit()
        return movie

    def delete_movie(self, movie_id: int) -> None:
        movie = Movie.query.get(movie_id)
        if not movie:
            raise LookupError("Movie not found")
        db.session.delete(movie)
        db.session.commit()