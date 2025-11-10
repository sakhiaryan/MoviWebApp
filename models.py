# models.py
from __future__ import annotations
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """
    User model representing an account that owns a list of favorite movies.
    """
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    movies = db.relationship(
        "Movie",
        backref="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} name='{self.name}'>"

    def __str__(self) -> str:
        return self.name


class Movie(db.Model):
    """
    Movie model representing one favorite movie that belongs to a user.
    """
    __tablename__ = "movie"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    year = db.Column(db.String(10), nullable=True)
    imdb_id = db.Column(db.String(32), nullable=True)
    poster_url = db.Column(db.String(512), nullable=True)
    rating = db.Column(db.Integer, nullable=True)  # 1..10 (user-given)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return f"<Movie id={self.id} title='{self.title}' user_id={self.user_id}>"

    def __str__(self) -> str:
        return f"{self.title} ({self.year or 'n/a'})"