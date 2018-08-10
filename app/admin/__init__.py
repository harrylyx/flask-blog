from flask_admin import Admin
from .routes import MyAdminIndexView


admin = Admin(name='后台', index_view=routes.MyAdminIndexView(), base_template='admin/my_master.html')




