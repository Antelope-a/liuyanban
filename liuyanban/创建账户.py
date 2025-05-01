from app import create_app
from extensions import db
from models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    admin = User(
        username="Antelope",
        password=generate_password_hash("Makise1048596"),  # 替换为实际密码
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("管理员账户创建成功！")
