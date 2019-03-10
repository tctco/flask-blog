import os

class Config:
    SECRET_KEY = '584cd8b1a18aa2f4a73244f3e4c59a96'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///site.db'
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "tctco2018@gmail.com"#os.environ.get('MAIL_USER')
    MAIL_PASSWORD = "dnjgvezbvdcrnqgt"#os.environ.get('MAIL_PASS')