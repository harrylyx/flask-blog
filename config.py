import os
basedir = 'mysql+pymysql://root:lyx15lyx@localhost:3306/blog'

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or basedir
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = 'smtp.163.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = 'your-email@163.com'
    MAIL_PASSWORD = "your-password"
    ADMINS = ['your-email@163.com']
    POSTS_PER_PAGE = 25

