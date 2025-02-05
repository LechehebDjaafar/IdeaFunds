from flask import Flask, render_template, url_for, redirect, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from models import db, User, Project, Message  # تأكد من إضافة Message هنا
from config import Config

# إنشاء التطبيق
app = Flask(__name__)
app.config.from_object(Config)

# تهيئة الإضافات
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# تحميل المستخدم الحالي
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# الصفحة الرئيسية
@app.route('/')
def home():
    return render_template('base.html')

# تسجيل حساب جديد
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        role = request.form['role']
        user = User(username=username, email=email, password=password, role=role)
        db.session.add(user)
        db.session.commit()
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html')

# تسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

# لوحة التحكم
@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'student':
        projects = Project.query.filter_by(user_id=current_user.id).all()
        return render_template('dashboard.html', projects=projects)
    elif current_user.role == 'investor':
        projects = Project.query.all()
        return render_template('projects_list.html', projects=projects)

# إضافة مشروع جديد
@app.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    if current_user.role != 'student':
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        required_amount = float(request.form['required_amount'])
        sector = request.form['sector']
        project = Project(
            title=title,
            description=description,
            required_amount=required_amount,
            sector=sector,
            user=current_user
        )
        db.session.add(project)
        db.session.commit()
        flash('Project added successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('project_form.html')

# عرض قائمة المشاريع مع الفلترة
@app.route('/projects', methods=['GET'])
@login_required
def projects():
    sector = request.args.get('sector', None)
    min_amount = request.args.get('min_amount', None)
    max_amount = request.args.get('max_amount', None)

    query = Project.query

    if sector:
        query = query.filter_by(sector=sector)
    if min_amount:
        query = query.filter(Project.required_amount >= float(min_amount))
    if max_amount:
        query = query.filter(Project.required_amount <= float(max_amount))

    projects = query.all()
    return render_template('projects_list.html', projects=projects)

# إرسال رسالة
@app.route('/send_message/<int:receiver_id>', methods=['GET', 'POST'])
@login_required
def send_message(receiver_id):
    receiver = User.query.get_or_404(receiver_id)
    if request.method == 'POST':
        content = request.form['content']
        message = Message(sender=current_user, receiver=receiver, content=content)
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
        return redirect(url_for('dashboard'))
    return render_template('send_message.html', receiver=receiver)

# عرض الرسائل
@app.route('/messages')
@login_required
def messages():
    messages = Message.query.filter(
        (Message.sender_id == current_user.id) | (Message.receiver_id == current_user.id)
    ).all()
    return render_template('messages.html', messages=messages)

# عرض تفاصيل المشروع
@app.route('/project/<int:project_id>')
@login_required
def project_details(project_id):
    project = Project.query.get_or_404(project_id)
    return render_template('project_details.html', project=project)

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True)