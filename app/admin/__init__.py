from flask_admin import Admin
from .routes import MyAdminIndexView, ArticleAdmin
from app.models import Article
from ..models import db

admin = Admin(name='后台', index_view=routes.MyAdminIndexView(), base_template='admin/my_master.html')

admin.add_view(ArticleAdmin(Article, db.session, name='文章'))


