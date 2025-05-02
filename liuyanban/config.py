import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'messages.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'uploads')  # 上传目录
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # 允许的图片类型
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 限制为2MB
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-123'
    ENABLE_QUESTION = True  # 是否启用问题验证
