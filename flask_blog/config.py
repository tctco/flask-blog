import json
import os

with open('/etc/flask_blog_config.json') as config_file:
    config = json.load(config_file)

class Config:
    SECRET_KEY = config.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = config.get('SQLALCHEMY_DATABASE_URI')
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "tctco2018@gmail.com"#os.environ.get('MAIL_USER')
    MAIL_PASSWORD = "dnjgvezbvdcrnqgt"#os.environ.get('MAIL_PASS')
