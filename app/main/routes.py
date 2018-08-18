from flask import render_template, request
from app.models import Article, Category, Tag
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
    categories = Category.query.all()
    return render_template('main/index.html', articles=articles, categories=categories,
                           pagination=pagination, endpoint='main.index')


@bp.route('/article/<int:id>/', methods=['GET', 'POST'])
def article(id):
    article = Article.query.get_or_404(id)
    next = next_article(article)
    prev = prev_article(article)

    return render_template('main/article.html', article=article,  category_id=article.category_id, next_article=next,
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


@bp.route('/category/<int:id>/')
def category(id):
    page = request.args.get('page', 1, type=int)
    pagination = Category.query.get_or_404(id).articles.order_by(
        Article.created.desc()).paginate(
        page, per_page=Article.PER_PAGE,
        error_out=False)
    articles = pagination.items
    return render_template('main/index.html', articles=articles,
                           pagination=pagination, endpoint='.category',
                           id=category.id, category_id=category.id)


@bp.route('/tag/<name>/')
def tag(name):
    page = int(request.args.get('page', 1))
    # 若name为非ASCII字符，传入时一般是经过URL编码的
    # 若name为URL编码，则需要解码为Unicode
    # URL编码判断方法：若已为URL编码, 再次编码会在每个码之前出现`%25`
    # _name = to_bytes(name, 'utf-8')
    # if urllib.quote(_name).count('%25') > 0:
    #     name = urllib.unquote(_name)
    tag = Tag.query.filter_by(name=name).first_or_404()
    _query = Article.query.filter(Article.tags.any(id=tag.id)).order_by(
        Article.created.desc())
    pagination = _query.paginate(
        page, per_page=Article.PER_PAGE,
        error_out=False)
    articles = pagination.items
    return render_template('main/index.html',
                           articles=articles,
                           tag=tag,
                           pagination=pagination, endpoint='.index', select_tag=tag)
