import re
from functools import reduce
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from flask import url_for
from flask_sqlalchemy import BaseQuery
from jinja2.filters import do_striptags, do_truncate
from markdown import markdown
from app import db, login

pattern_hasmore = re.compile(r'<!--more-->', re.I)


def markitup(text):
    """
    把Markdown转换为HTML
    """
    exts = ['markdown.extensions.extra', 'markdown.extensions.codehilite', \
            'markdown.extensions.tables', 'markdown.extensions.toc']
    ret = markdown(text, extensions=exts)
    return ret


def keywords_split(keywords):
    return keywords.replace(u',', ' ') \
        .replace(u';', ' ') \
        .replace(u'+', ' ') \
        .replace(u'；', ' ') \
        .replace(u'，', ' ') \
        .replace(u'　', ' ') \
        .split(' ')


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


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


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    articles = db.relationship('Article', backref='category', lazy='dynamic')

    __mapper_args__ = {'order_by': [name]}

    @property
    def link(self):
        return url_for('main.category', id=self.id, _external=True)

    @property
    def count(self):
        cates = db.session.query(Category.id).all()
        cate_ids = [cate.id for cate in cates]
        return Article.query.public().filter(Article.category_id.in_(cate_ids)).count()

    def __repr__(self):
        return '<Category %r>' % self.name

    def __str__(self):
        return self.name


article_tags_table = db.Table('article_tags',
                              db.Column('article_id', db.Integer, db.ForeignKey('articles.id', ondelete='CASCADE')),
                              db.Column('tag_id', db.Integer, db.ForeignKey('tags.id', ondelete='CASCADE')))


class TagQuery(BaseQuery):

    def search(self, keyword):
        keyword = u'%{0}%'.format(keyword.strip())
        return self.filter(Tag.name.ilike(keyword))


class Tag(db.Model):
    """标签"""
    __tablename__ = 'tags'
    query_class = TagQuery
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, index=True, nullable=False)

    __mapper_args__ = {'order_by': [id.desc()]}

    @property
    def link(self):
        return url_for('main.tag', name=self.name.lower(), _external=True)

    def __repr__(self):
        return '<Tag %r>' % self.name

    def __str__(self):
        return self.name

    @property
    def count(self):
        return Article.query.public().filter(Article.tags.any(id=self.id)).count()


class ArticleQuery(BaseQuery):

    def public(self):
        return self.filter_by(published=True)

    def search(self, keyword):
        criteria = []

        for keyword in keywords_split(keyword):
            keyword = u'%{0}%'.format(keyword)
            criteria.append(db.or_(Article.title.ilike(keyword), ))

        q = reduce(db.or_, criteria)
        return self.public().filter(q)

    def archives(self, year, month):
        if not year:
            return self

        criteria = [db.extract('year', Article.created) == year]
        if month:
            criteria.append(db.extract('month', Article.created) == month)

        q = reduce(db.and_, criteria)
        return self.public().filter(q)


class Article(db.Model):
    PER_PAGE = 10

    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256))
    summary = db.Column(db.Text)
    content = db.Column(db.Text)
    content_html = db.Column(db.Text)
    # hin = db.Column(db.Integer)

    created = db.Column(db.DateTime())
    author_id = db.Column(db.Integer, db.ForeignKey(User.id))
    category_id = db.Column(db.Integer(), db.ForeignKey(Category.id), nullable=False, )
    tags = db.relationship(Tag, secondary=article_tags_table, backref=db.backref("articles"))

    __mapper_args__ = {'order_by': [id.desc()]}

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

    @staticmethod
    def before_insert(mapper, connection, target):
        def _format(_html):
            return do_truncate(do_striptags(_html), length=200)

        value = target.content


    @staticmethod
    def on_change_content(target, value, oldvalue, initiator):
        target.content_html = markitup(value)

        # TODO 有问题
        def _format(_html):
            return do_truncate(do_striptags(_html), length=200)


db.event.listen(Article.content, 'set', Article.on_change_content)
db.event.listen(Article, 'before_insert', Article.before_insert)
