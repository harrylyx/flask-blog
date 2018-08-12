import datetime
from flask import redirect, url_for, render_template, flash, request
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app import app
from app.models import User
from app.admin.forms import LoginForm
from wtforms.fields import TextAreaField


def format_datetime(self, request, obj, fieldname, *args, **kwargs):
    return getattr(obj, fieldname).strftime("%Y-%m-%d %H:%M")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index')
        return redirect(next_page)
    return render_template('admin/login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        if not current_user.is_authenticated and current_user.username == "cabbage":
            return redirect(url_for('login'))
        # if not current_user.is_administrator():
        #     return redirect(url_for('index'))
        return super(MyAdminIndexView, self).index()


class ArticleAdmin(ModelView):
    create_template = "admin/model/a_create.html"
    edit_template = "admin/model/a_edit.html"

    column_list = ('title', 'created', 'category', 'tags')

    form_excluded_columns = ('author', 'content_html', 'created')

    column_searchable_list = ('title',)

    column_formatters = dict(created=format_datetime)

    form_create_rules = (
        'title', 'category', 'tags', 'content'
    )
    form_edit_rules = form_create_rules

    form_overrides = dict(
        summary=TextAreaField)

    form_widget_args = {
        'title': {'style': 'width:480px;'},
    }

    column_labels = dict(
        title='标题',
        category='分类',
        tags='标签',
        content='正文',
        created='创建时间',
    )

    def is_accessible(self):
        if current_user.is_authenticated and current_user.username == "cabbage":
            return True
        return False

    # Model handlers
    def on_model_change(self, form, model, is_created):
        if is_created:
            model.author_id = current_user.id
            model.created = datetime.datetime.now()


class CategoryAdmin(ModelView):
    # create_template = "admin/model/a_create.html"
    # edit_template = "admin/model/a_edit.html"

    column_list = ('name',)

    column_searchable_list = ('name',)

    column_labels = dict(
        name='名称',
    )

    form_widget_args = {
        'name': {'style': 'width:320px;'},
    }

    def is_accessible(self):
        if current_user.is_authenticated and current_user.username == "cabbage":
            return True
        return False


class TagAdmin(ModelView):
    # create_template = "admin/model/a_create.html"
    # edit_template = "admin/model/a_edit.html"

    column_list = ('name',)

    column_searchable_list = ('name',)

    form_excluded_columns = 'articles'

    # column_formatters = dict(view_on_site=view_on_site)

    column_labels = dict(
        name='名称',
    )

    form_widget_args = {
        'name': {'style': 'width:320px;'},
    }

    def is_accessible(self):
        if current_user.is_authenticated and current_user.username == "cabbage":
            return True
        return False

