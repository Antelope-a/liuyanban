from datetime import datetime
from extensions import db
from flask_login import UserMixin  # 新增导入

class User(db.Model, UserMixin):  # 继承 UserMixin
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    username = db.Column(db.String(50), default='Anonymous')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    images = db.relationship('Image', backref='message', cascade='all, delete-orphan')  # 关联图片
    parent_id = db.Column(db.Integer, db.ForeignKey('message.id'))  # 自引用外键
    replies = db.relationship('Message', backref=db.backref('parent', remote_side=[id]))
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 修正后的外键
    admin = db.relationship('User', backref='announcements')
class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False, unique=True)
    answer = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)  # 是否启用该问题
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
