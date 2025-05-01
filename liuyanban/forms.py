# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, FileField, PasswordField, HiddenField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileAllowed

class MessageForm(FlaskForm):
    content = TextAreaField('留言内容', validators=[DataRequired(), Length(max=200)])
    username = StringField('昵称（可选）', validators=[Length(max=50)])
    images = FileField('上传图片（最多5张）', validators=[
        FileAllowed(['png', 'jpg', 'jpeg', 'gif'], '仅允许图片文件！'),
    ], render_kw={"multiple": True})  # 允许选择多个文件
    submit = SubmitField('提交留言')

class AdminLoginForm(FlaskForm):
    username = StringField('管理员账号', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])  # 使用 PasswordField
    submit = SubmitField('登录')

class ReplyForm(FlaskForm):
    content = TextAreaField('回复内容', validators=[DataRequired(), Length(max=200)])
    username = StringField('昵称（可选）', validators=[Length(max=50)])
    submit = SubmitField('提交回复')

class SearchForm(FlaskForm):
    keyword = StringField('搜索留言', validators=[DataRequired()])
    submit = SubmitField('搜索')

class AnnouncementForm(FlaskForm):
    title = StringField('公告标题', validators=[
        DataRequired(), 
        Length(max=100, message="标题不能超过100字")
    ])
    content = TextAreaField('公告内容', validators=[
        DataRequired(),
        Length(max=1000, message="内容不能超过1000字")
    ])
    submit = SubmitField('发布公告')
    # 添加编辑模式标识（可选）
    is_edit = HiddenField('是否为编辑模式', default=False)
