"""Data access layer for MoviWebApp using SQLAlchemy ORM."""

from typing import List, Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy import func
from models import db, User, Movie


class DataManager:
    """Encapsulates CRUD operations for users and movies."""

    # -------------------- User methods --------------------

    def create_user(self, name: str) -> Tuple[Optional[User], Optional[str]]:
        """Create a new user if the name is valid and not taken (case-insensitive).

        Returns:
            (user, error_message) where user is created User or None on error.
        """
        try:
            clean = (name or "").strip()
            if not clean:
                return None, "User name cannot be empty."

            # case-insensitive duplicate check
            existing = User.query.filter(func.lower(User.name) == clean.lower()).first()
            if existing:
                return None, "User name already exists."

            user = User(name=clean)
            db.session.add(user)
            db.session.commit()
            return user, None
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Database error while creating user: {e}"

    def get_users(self) -> List[User]:
        """Return all users ordered by name."""
        return User.query.order_by(User.name.asc()).all()

    def get_user(self, user_id: int) -> Optional[User]:
        """Return user by id or None."""
        return User.query.get(user_id)

    # -------------------- Movie methods --------------------

    def get_movies(self, user_id: int) -> List[Movie]:
        """Return movies for a user ordered by title."""
        return Movie.query.filter_by(user_id=user_id).order_by(Movie.title.asc()).all()

    def add_movie(
        self,
        user_id: int,
        title: str,
        year: Optional[str] = None,
        poster_url: Optional[str] = None,
        rating: Optional[int] = None,
    ) -> Tuple[Optional[Movie], Optional[str]]:
        """Add a movie for a user with validation.

        Validation:
          - title not empty
          - rating either None or integer in [1, 10]
          - no duplicate title for same user (case-insensitive)

        Returns:
            (movie, error_message)
        """
        try:
            # Validate user
            user = User.query.get(user_id)
            if not user:
                return None, "User not found."

            clean_title = (title or "").strip()
            if not clean_title:
                return None, "Movie title cannot be empty."

            if rating is not None:
                try:
                    rating = int(rating)
                except ValueError:
                    return None, "Rating must be an integer between 1 and 10."
                if rating < 1 or rating > 10:
                    return None, "Rating must be between 1 and 10."

            # case-insensitive duplicate check for this user
            dup = (
                Movie.query.filter(
                    Movie.user_id == user_id,
                    func.lower(Movie.title) == clean_title.lower(),
                )
                .limit(1)
                .first()
            )
            if dup:
                return None, "This user already has a movie with the same title."

            movie = Movie(
                user_id=user_id,
                title=clean_title,
                year=(year or None),
                poster_url=(poster_url or None),
                rating=rating,
            )
            db.session.add(movie)
            db.session.commit()
            return movie, None
        except IntegrityError as e:
            db.session.rollback()
            return None, f"Duplicate constraint violated: {e}"
        except SQLAlchemyError as e:
            db.session.rollback()
            return None, f"Database error while adding movie: {e}"

    def update_movie(
        self,
        movie_id: int,
        *,
        title: Optional[str] = None,
        year: Optional[str] = None,
        poster_url: Optional[str] = None,
        rating: Optional[int] = None,
    ) -> Optional[str]:
        """Update fields of a movie with validation; returns error message or None on success."""
        try:
            movie = Movie.query.get(movie_id)
            if not movie:
                return "Movie not found."

            if title is not None:
                clean = title.strip()
                if not clean:
                    return "Title cannot be empty."
                # check duplicates for same user if title changed
                if clean.lower() != movie.title.lower():
                    dup = (
                        Movie.query.filter(
                            Movie.user_id == movie.user_id,
                            func.lower(Movie.title) == clean.lower(),
                            Movie.id != movie.id,
                        )
                        .limit(1)
                        .first()
                    )
                    if dup:
                        return "This user already has a movie with that title."
                movie.title = clean

            if year is not None:
                movie.year = year.strip() or None

            if poster_url is not None:
                movie.poster_url = poster_url.strip() or None

            if rating is not None:
                try:
                    rating_val = int(rating)
                except ValueError:
                    return "Rating must be an integer between 1 and 10."
                if rating_val < 1 or rating_val > 10:
                    return "Rating must be between 1 and 10."
                movie.rating = rating_val

            db.session.commit()
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            return f"Database error while updating movie: {e}"

    def delete_movie(self, movie_id: int) -> Optional[str]:
        """Delete a movie by id; returns error message or None on success."""
        try:
            movie = Movie.query.get(movie_id)
            if not movie:
                return "Movie not found."
            db.session.delete(movie)
            db.session.commit()
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            return f"Database error while deleting movie: {e}"