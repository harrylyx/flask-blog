from flask import render_template, request
from app import login
from app.models import User, Article
from . import bp


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    page = request.args.get('page', 1, type=int)
    pagination = Article.query.order_by(
        Article.created.desc()).paginate(page,
                                         per_page=Article.PER_PAGE,
                                         error_out=False)
    articles = pagination.items
    return render_template('main/index.html', articles=articles,
                           pagination=pagination, endpoint='main.index')


@bp.route('/article/<int:id>/', methods=['GET', 'POST'])
def article(id):
    article = Article.query.get_or_404(id)
    next = next_article(article)
    prev = prev_article(article)

    page = request.args.get('page', 1, type=int)

    return render_template('main/article.html', article=article, next_article=next,
                           prev_article=prev, endpoint='.article', id=article.id)


def next_article(article):
    """
    获取本篇文章的下一篇
    :param article: article
    :return: next article
    """
    article_list = Article.query.order_by(Article.created.desc()).all()
    articles = [article for article in article_list]
    if articles[0] != article:
        next_post = articles[articles.index(article) - 1]
        return next_post
    return None


def prev_article(article):
    """
    获取本篇文章的上一篇
    :param article: article
    :return: prev article
    """
    article_list = Article.query.order_by(Article.created.desc()).all()
    articles = [article for article in article_list]
    if articles[-1] != article:
        prev_article = articles[articles.index(article) + 1]
        return prev_article
    return None


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
