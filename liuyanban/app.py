from flask import Flask
from config import Config
from extensions import db, login_manager
import os  # 关键修复：导入 os 模块

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        # 确保上传目录存在
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)  # 依赖 os 模块
        from models import User
        from models import Message, Announcement, Image
        from routes import main_bp
        db.create_all()
        app.register_blueprint(main_bp)
        login_manager.init_app(app)
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
