import os

class Config:
    SECRET_KEY = os.environ.get('UNLESS-YOU-USE-SOMETHING-SOME-OTHER-TRIBE-WILL-KILL-HIM') or 'your_super_secret_key_here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')