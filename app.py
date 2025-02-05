from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required

# إنشاء تطبيق Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # استخدم مفتاحًا أمانًا قويًا في الإنتاج
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إعداد قاعدة البيانات
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# إعداد إدارة تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# نموذج المستخدم
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20))  # "student" أو "investor"

# نموذج المشروع
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))  # اختياري
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('projects', lazy=True))

# تحميل المستخدم بناءً على ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# رابط للتسجيل
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_user = User(username=username, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()

        flash('تم إنشاء الحساب بنجاح!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# رابط لتسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('home'))
        else:
            flash('فشل تسجيل الدخول. يرجى التحقق من البريد الإلكتروني وكلمة المرور.', 'danger')

    return render_template('login.html')

# رابط لتسجيل الخروج
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('تم تسجيل الخروج بنجاح!', 'success')
    return redirect(url_for('login'))

# الصفحة الرئيسية (للمستخدمين المسجلين فقط)
@app.route('/')
@login_required
def home():
    return render_template('home.html')

# رابط لعرض المشاريع
@app.route('/projects')
@login_required
def projects():
    all_projects = Project.query.all()
    return render_template('projects.html', projects=all_projects)

# رابط لإضافة مشروع جديد
@app.route('/add_project', methods=['GET', 'POST'])
@login_required
def add_project():
    if current_user.role != 'student':  # فقط الطلاب يمكنهم إضافة مشاريع
        flash('فقط الطلاب يمكنهم إضافة مشاريع!', 'danger')
        return redirect(url_for('projects'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        target_amount = float(request.form['target_amount'])
        image_url = request.form.get('image_url', '')  # اختياري

        new_project = Project(
            title=title,
            description=description,
            target_amount=target_amount,
            image_url=image_url,
            user_id=current_user.id
        )
        db.session.add(new_project)
        db.session.commit()

        flash('تم إنشاء المشروع بنجاح!', 'success')
        return redirect(url_for('projects'))

    return render_template('add_project.html')

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True)