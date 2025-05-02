from flask import (
    Blueprint, render_template, redirect, url_for,
    request, send_from_directory, flash, session, current_app, abort
)
from werkzeug.utils import secure_filename
from functools import wraps
import uuid
import os
from extensions import db, login_manager
from models import Message, Image, Announcement, User, Question
from forms import MessageForm, AdminLoginForm, ReplyForm, SearchForm, AnnouncementForm, QuestionForm
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from flask_login import current_user, login_required, login_user
from werkzeug.security import check_password_hash, generate_password_hash
# 定义蓝图
main_bp = Blueprint('main', __name__)

# ================= 管理功能路由 =================
@main_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)  # 设置用户会话
            return redirect(url_for('main.admin_dashboard'))
        else:
            flash('账号或密码错误', 'danger')
    return render_template('admin/login.html', form=form)

@main_bp.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('main.index'))

# 登录装饰器（用于权限控制）
def admin_required(f):
    @wraps(f)
    @login_required  # 确保用户已登录
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:  # 检查是否是管理员
            abort(403)  # 权限不足
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/admin/message/manage')
@admin_required
def manage_messages():
    # 获取搜索关键词
    search_keyword = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    
    # 构建查询
    query = Message.query
    if search_keyword:
        search_pattern = f"%{search_keyword}%"
        query = query.filter(
            or_(
                Message.content.ilike(search_pattern),
                Message.username.ilike(search_pattern)
            )
        )
    
    # 分页查询（每页10条）
    messages = query.order_by(Message.timestamp.desc()).paginate(page=page, per_page=10)
    return render_template(
        'admin/manage_messages.html',
        messages=messages,
        q=search_keyword
    )

@main_bp.route('/admin/message/delete/<int:message_id>', methods=['POST'])
@admin_required
def delete_message(message_id):
    # 获取留言对象
    message = Message.query.get_or_404(message_id)
    
    # 删除关联的图片文件
    upload_dir = current_app.config['UPLOAD_FOLDER']
    for image in message.images:
        image_path = os.path.join(upload_dir, image.filename)
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
        except Exception as e:
            current_app.logger.error(f"删除图片失败: {e}")
    
    # 删除数据库记录
    try:
        db.session.delete(message)
        db.session.commit()
        flash('留言及关联图片已删除', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"数据库操作失败: {e}")
        flash('删除失败，请稍后重试', 'danger')
    
    # 保留搜索关键词并重定向
    return redirect(url_for('main.manage_messages', q=request.args.get('q', '')))

# ==============================
# 辅助函数
# ==============================
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@main_bp.route('/answer-question', methods=['GET', 'POST'])
def answer_question():
    if not current_app.config.get('ENABLE_QUESTION', False):
        session['question_passed'] = True
        return redirect(url_for('main.index'))
    try:
        question = Question.query.filter_by(is_active=True).order_by(db.func.random()).first()
    except Exception as e:
        current_app.logger.error(f"数据库查询失败: {e}")
        flash('系统错误，请稍后重试', 'danger')
        return redirect(url_for('main.index'))

    if not question:
        session['question_passed'] = True
        session.permanent = True
        session.modified = True
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip()
        if user_answer.lower() == question.answer.lower():
            session['question_passed'] = True
            session.permanent = True
            session.modified = True  # 强制保存会话
            return redirect(url_for('main.index'))
        else:
            flash('答案错误，请重试', 'danger')

    return render_template('answer_question.html', question=question)
    # 确保装饰器定义在路由之前
def check_question_answered(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果未通过验证且功能已启用
        if not session.get('question_passed') and current_app.config.get('ENABLE_QUESTION', False):
            return redirect(url_for('main.answer_question'))
        return f(*args, **kwargs)
    return decorated_function

@main_bp.route('/', methods=['GET', 'POST'])
@check_question_answered
def index():
    form = MessageForm()
    page = request.args.get('page', 1, type=int)  # 新增分页参数
    per_page = 10  # 每页显示数量
    # POST 请求处理（提交留言）
    if form.validate_on_submit():
        # 创建留言
        message = Message(
            content=form.content.data,
            username=form.username.data or 'Anonymous'
        )
        db.session.add(message)
        db.session.commit()  # 先提交以获取 message.id
        
        # 处理上传的图片（最多5张）
        uploaded_files = request.files.getlist('images')
        max_images = 5
        for i, file in enumerate(uploaded_files):
            if i >= max_images:
                break
            if file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                unique_name = f"{uuid.uuid4()}_{filename}"
                upload_dir = current_app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)
                file.save(os.path.join(upload_dir, unique_name))
                image = Image(filename=unique_name, message_id=message.id)
                db.session.add(image)
        
        db.session.commit()
        return redirect(url_for('main.index'))  # 重定向到 GET 请求
    
    # GET 请求处理（显示页面）
    messages = Message.query.order_by(
        Message.timestamp.desc()
    ).paginate(page=page, per_page=per_page)  # 修改为分页查询

    announcements = Announcement.query.order_by(
        Announcement.timestamp.desc()
    ).limit(3).all()

    return render_template(
        'index.html',
        form=form,
        messages=messages,
        announcements=announcements  # 确保传递公告数据
    )

@main_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
@main_bp.route('/reply/<int:parent_id>', methods=['GET', 'POST'])
@check_question_answered
def reply_message(parent_id):
    """处理留言回复"""
    parent_message = Message.query.get_or_404(parent_id)  # 获取父级留言
    form = ReplyForm()  # 使用回复表单
    
    if form.validate_on_submit():
        # 创建回复留言
        reply = Message(
            content=form.content.data,
            username=form.username.data or 'Anonymous',
            parent_id=parent_id  # 关联父级留言
        )
        db.session.add(reply)
        db.session.commit()
        return redirect(url_for('main.index'))
    
    return render_template('reply.html', form=form, parent=parent_message)
#搜索
@main_bp.route('/search', methods=['GET', 'POST'])
@check_question_answered
def search():
    form = SearchForm()
    results = []
    if form.validate_on_submit():
        keyword = form.keyword.data
        search_pattern = f"%{keyword}%"
        # 关键修改：预加载关联图片
        results = Message.query.options(joinedload(Message.images)).filter(
            or_(
                Message.content.like(search_pattern),
                Message.username.like(search_pattern)
            )
        ).order_by(Message.timestamp.desc()).all()
    
    return render_template('search.html', form=form, results=results)

@main_bp.route('/admin/post_announcement', methods=['GET', 'POST'])
@admin_required
def post_announcement():
    form = AnnouncementForm()
    if form.validate_on_submit():
        # 获取当前管理员用户（假设session存储了user_id）
        admin_id = session.get('user_id')
        announcement = Announcement(
            title=form.title.data,
            content=form.content.data,
            admin_id=admin_id
        )
        db.session.add(announcement)
        db.session.commit()
        flash('公告发布成功', 'success')
        return redirect(url_for('main.manage_announcements'))
    return render_template('admin/post_announcement.html', form=form)

@main_bp.route('/admin/announcements')
@admin_required
def manage_announcements():
    page = request.args.get('page', 1, type=int)
    announcements = Announcement.query.order_by(
        Announcement.timestamp.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/manage_announcements.html', 
                         announcements=announcements)

@main_bp.route('/admin/delete_announcement/<int:id>', methods=['POST'])
@admin_required
@login_required
def delete_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    flash('公告已删除', 'success')
    return redirect(url_for('main.manage_announcements'))

@main_bp.route('/admin/edit_announcement/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_announcement(id):
    announcement = Announcement.query.get_or_404(id)
    form = AnnouncementForm(obj=announcement)  # 自动填充表单
    
    if form.validate_on_submit():
        form.populate_obj(announcement)  # 自动更新对象
        db.session.commit()
        flash('公告已更新', 'success')
        return redirect(url_for('main.manage_announcements'))
    
    return render_template('admin/edit_announcement.html', 
                         form=form, 
                         announcement=announcement)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main_bp.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """管理员导航面板"""
    return render_template('admin/dashboard.html')

@main_bp.route('/admin/questions')
@admin_required
def manage_questions():
    questions = Question.query.order_by(Question.timestamp.desc()).all()
    return render_template('admin/manage_questions.html', questions=questions)

@main_bp.route('/admin/question/add', methods=['GET', 'POST'])
@admin_required
def add_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            content=form.content.data,
            answer=form.answer.data
        )
        db.session.add(question)
        db.session.commit()
        flash('问题已添加', 'success')
        return redirect(url_for('main.manage_questions'))
    return render_template('admin/edit_question.html', form=form)

@main_bp.route('/admin/question/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_question(id):
    question = Question.query.get_or_404(id)
    form = QuestionForm(obj=question)
    if form.validate_on_submit():
        form.populate_obj(question)
        db.session.commit()
        flash('问题已更新', 'success')
        return redirect(url_for('main.manage_questions'))
    return render_template('admin/edit_question.html', form=form, question=question)

@main_bp.route('/admin/question/toggle/<int:id>', methods=['POST'])
@admin_required
def toggle_question(id):
    question = Question.query.get_or_404(id)
    question.is_active = not question.is_active
    db.session.commit()
    return redirect(url_for('main.manage_questions'))

@main_bp.route('/admin/question/delete/<int:id>', methods=['POST'])
@admin_required
def delete_question(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    flash('问题已删除', 'success')
    return redirect(url_for('main.manage_questions'))
