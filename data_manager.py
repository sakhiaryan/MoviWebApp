# data_manager.py
from __future__ import annotations
import logging
import os
from typing import List, Optional, Tuple, Dict, Any

import requests
from sqlalchemy.exc import SQLAlchemyError

from models import db, User, Movie

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DataManager:
    """
    Data access and business logic layer for MoviWebApp.
    All DB operations are wrapped with error handling.
    """

    # ---------- Helpers / Validation ----------

    @staticmethod
    def _normalize_name(name: str) -> str:
        return (name or "").strip()

    @staticmethod
    def _validate_movie_input(title: Optional[str], rating: Optional[str | int]) -> Tuple[str, Optional[int]]:
        """
        Shared validation for add_movie & update_movie.
        Ensures title non-empty and rating is None or integer 1..10.
        """
        t = (title or "").strip()
        if not t:
            raise ValueError("Title cannot be empty.")

        if rating is None or rating == "":
            return t, None

        try:
            r = int(rating)
        except (TypeError, ValueError):
            raise ValueError("Rating must be an integer between 1 and 10.")

        if not (1 <= r <= 10):
            raise ValueError("Rating must be between 1 and 10.")

        return t, r

    # ---------- Users ----------

    def get_users(self) -> List[User]:
        """
        Returns all users ordered by name.
        Never raises to the caller; logs and returns [] on error.
        """
        try:
            return User.query.order_by(User.name.asc()).all()
        except SQLAlchemyError as e:
            logger.exception("get_users failed: %s", e)
            return []

    def create_user(self, name: str) -> Tuple[Optional[User], Optional[str]]:
        """
        Creates a user with unique name. Returns (user, error_message).
        """
        try:
            norm = self._normalize_name(name)
            if not norm:
                return None, "User name cannot be empty."

            # Duplicate check
            if User.query.filter(User.name.ilike(norm)).first():
                return None, f"User '{norm}' already exists."

            user = User(name=norm)
            db.session.add(user)
            db.session.commit()
            return user, None
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.exception("create_user failed: %s", e)
            return None, "Database error while creating user."

    # ---------- Movies ----------

    def get_movies(self, user_id: int) -> List[Movie]:
        """
        Returns movies for a given user (sorted by title).
        Returns [] on error.
        """
        try:
            return Movie.query.filter_by(user_id=user_id).order_by(Movie.title.asc()).all()
        except SQLAlchemyError as e:
            logger.exception("get_movies failed: %s", e)
            return []

    def _fetch_omdb(self, title: str) -> Dict[str, Any]:
        """
        Fetches movie data from OMDb by title. Returns dict with keys:
        title, year, imdb_id, poster_url. Missing fields set to None.
        Requires OMDB_API_KEY in environment or .env
        """
        api_key = os.getenv("OMDB_API_KEY")
        if not api_key:
            logger.warning("OMDB_API_KEY not set. Skipping external fetch.")
            return {"title": title, "year": None, "imdb_id": None, "poster_url": None}

        try:
            resp = requests.get(
                "https://www.omdbapi.com/",
                params={"t": title, "apikey": api_key},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if str(data.get("Response")).lower() == "true":
                return {
                    "title": data.get("Title") or title,
                    "year": data.get("Year"),
                    "imdb_id": data.get("imdbID"),
                    "poster_url": (data.get("Poster") if data.get("Poster") not in (None, "N/A") else None),
                }
            else:
                # Fallback to user-provided title
                return {"title": title, "year": None, "imdb_id": None, "poster_url": None}
        except Exception as e:
            logger.exception("OMDb request failed: %s", e)
            return {"title": title, "year": None, "imdb_id": None, "poster_url": None}

    def add_movie(self, user_id: int, title: str, rating: Optional[str | int]) -> Tuple[Optional[Movie], Optional[str]]:
        """
        Adds a movie for a given user. Returns (movie, error_message).
        Validates duplicates per-user (case-insensitive).
        Uses OMDb to enrich metadata.
        """
        try:
            # Validate
            norm_title, norm_rating = self._validate_movie_input(title, rating)

            # Duplicate (same user)
            duplicate = (
                Movie.query.filter(Movie.user_id == user_id)
                .filter(Movie.title.ilike(norm_title))
                .first()
            )
            if duplicate:
                return None, f"Movie '{norm_title}' already exists for this user."

            # Enrich via OMDb
            meta = self._fetch_omdb(norm_title)

            movie = Movie(
                user_id=user_id,
                title=meta["title"],
                year=meta["year"],
                imdb_id=meta["imdb_id"],
                poster_url=meta["poster_url"],
                rating=norm_rating,
            )
            db.session.add(movie)
            db.session.commit()
            return movie, None
        except ValueError as ve:
            return None, str(ve)
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.exception("add_movie failed: %s", e)
            return None, "Database error while adding movie."

    def update_movie(self, movie_id: int, title: Optional[str], rating: Optional[str | int]) -> Tuple[Optional[Movie], Optional[str]]:
        """
        Updates title/rating for a movie. Returns (movie, error_message).
        Applies same validation as add_movie; duplicate protection within user scope.
        """
        try:
            movie = Movie.query.get(movie_id)
            if not movie:
                return None, "Movie not found."

            # If no new values provided, treat as no-op
            if (title is None or title.strip() == "") and (rating is None or rating == ""):
                return movie, None

            new_title, new_rating = self._validate_movie_input(title or movie.title, rating if rating is not None else movie.rating)

            # Duplicate check if title changed
            if new_title.lower() != (movie.title or "").lower():
                dup = (
                    Movie.query.filter(Movie.user_id == movie.user_id)
                    .filter(Movie.title.ilike(new_title))
                    .first()
                )
                if dup:
                    return None, f"Movie '{new_title}' already exists for this user."

            movie.title = new_title
            movie.rating = new_rating

            # (Optional) re-enrich if title changed
            if new_title.lower() != (movie.title or "").lower():
                meta = self._fetch_omdb(new_title)
                movie.title = meta["title"]
                movie.year = meta["year"]
                movie.imdb_id = meta["imdb_id"]
                movie.poster_url = meta["poster_url"]

            db.session.commit()
            return movie, None
        except ValueError as ve:
            return None, str(ve)
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.exception("update_movie failed: %s", e)
            return None, "Database error while updating movie."

    def delete_movie(self, movie_id: int) -> Optional[str]:
        """
        Deletes a movie by id. Returns error message or None on success.
        """
        try:
            movie = Movie.query.get(movie_id)
            if not movie:
                return "Movie not found."
            db.session.delete(movie)
            db.session.commit()
            return None
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.exception("delete_movie failed: %s", e)
            return "Database error while deleting movie."