from flask_admin import Admin
from .routes import MyAdminIndexView, ArticleAdmin, CategoryAdmin, TagAdmin
from app.models import Article, Category, Tag
from ..models import db

admin = Admin(name='后台', index_view=routes.MyAdminIndexView(), base_template='admin/my_master.html')

admin.add_view(ArticleAdmin(Article, db.session, name='文章'))
admin.add_view(CategoryAdmin(Category, db.session, name='分类'))
admin.add_view(TagAdmin(Tag, db.session, name='标签'))

