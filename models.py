from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True)

    # One-to-many: user -> movies
    movies = db.relationship("Movie", backref="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} name={self.name!r}>"

    def __str__(self):
        return self.name


class Movie(db.Model):
    __tablename__ = "movie"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(300), nullable=False)
    year = db.Column(db.String(10))         # optional
    poster_url = db.Column(db.String(500))  # optional

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"<Movie id={self.id} title={self.title!r} user_id={self.user_id}>"

    def __str__(self):
        return self.title