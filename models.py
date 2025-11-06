"""SQLAlchemy models for MoviWebApp."""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    """User of the MoviWeb application.

    Attributes:
        id: Primary key.
        name: Unique display name (case-insensitive uniqueness enforced in app logic).
        created_at: Creation timestamp (UTC).
    """

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    movies = db.relationship(
        "Movie",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Movie.title.asc()",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} name={self.name!r}>"

    def __str__(self) -> str:
        return self.name


class Movie(db.Model):
    """Movie favorited by a User.

    Attributes:
        id: Primary key.
        title: Movie title (not empty).
        year: Optional release year (string to allow ranges/unknown like 'N/A').
        poster_url: Optional poster URL.
        rating: Optional integer rating 1..10.
        user_id: Foreign key to user.
    """

    __tablename__ = "movie"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    year = db.Column(db.String(16), nullable=True)
    poster_url = db.Column(db.String(512), nullable=True)
    rating = db.Column(db.Integer, nullable=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user = db.relationship("User", back_populates="movies")

    # Optional DB-level uniqueness: no duplicate titles per user
    __table_args__ = (
        UniqueConstraint("user_id", "title", name="uq_movie_user_title"),
    )

    def __repr__(self) -> str:
        return f"<Movie id={self.id} title={self.title!r} user_id={self.user_id} rating={self.rating}>"

    def __str__(self) -> str:
        return self.title