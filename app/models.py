from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import url_for

class User(UserMixin, db.Model):
    """Represents Proected users."""

    # Set the name for table
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        """Define the string format for instance of User."""
        return "<Model User `{}`>".format(self.username)


class Article(db.Model):
    PER_PAGE = 10

    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256))
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    created = db.Column(db.DateTime())
    author_id = db.Column(db.Integer, db.ForeignKey(User.id))

    def __repr__(self):
        return '<Article %r>' % (self.title)

    @property
    def year(self):
        return int(self.created.year)

    @property
    def month_and_day(self):
        return str(self.created.month) + "-" + str(self.created.day)

    @property
    def link(self):
        return url_for('main.article', id=self.id, _external=True)

    @property
    def get_next(self):
        _query = db.and_(Article.category_id.in_([self.category.id]),
                         Article.id > self.id)
        return self.query.public().filter(_query) \
            .order_by(Article.id.asc()) \
            .first()

    @property
    def get_prev(self):
        _query = db.and_(Article.category_id.in_([self.category.id]),
                         Article.id < self.id)
        return self.query.public().filter(_query) \
            .order_by(Article.id.desc()) \
            .first()
