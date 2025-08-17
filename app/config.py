import os

class Config:
    SECRET_KEY = os.environ.get('CHECK-EXISTING-HASYAKB') or 'your_super_secret_key_here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False