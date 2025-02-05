from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from sqlalchemy import or_

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
    sector = db.Column(db.String(50))  # قطاع المشروع
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

        # التحقق من صحة الإدخالات
        if not username or not email or not password or not role:
            flash('يرجى ملء جميع الحقول.', 'danger')
            return redirect(url_for('register'))

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

# الصفحة الرئيسية
@app.route('/')
def home():
    return render_template('index.html')

# رابط لعرض المشاريع
@app.route('/projects')
@login_required
def projects():
    all_projects = Project.query.all()

    if not all_projects:
        flash('لا توجد مشاريع متاحة حاليًا.', 'info')

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

        # التحقق من صحة الإدخالات
        if not title or not description or target_amount <= 0:
            flash('يرجى ملء جميع الحقول بشكل صحيح.', 'danger')
            return redirect(url_for('add_project'))

        image_url = request.form.get('image_url', '')  # اختياري
        sector = request.form.get('sector', '')  # قطاع المشروع

        new_project = Project(
            title=title,
            description=description,
            target_amount=target_amount,
            image_url=image_url,
            sector=sector,
            user_id=current_user.id
        )
        db.session.add(new_project)
        db.session.commit()
        flash('تم إنشاء المشروع بنجاح!', 'success')
        return redirect(url_for('projects'))

    return render_template('add_project.html')

# لوحة تحكم الطالب
@app.route('/dashboard_student')
@login_required
def dashboard_student():
    if current_user.role != 'student':
        flash('ليس لديك إذن للوصول إلى هذه الصفحة!', 'danger')
        return redirect(url_for('home'))
    
    # استرجاع المشاريع الخاصة بالطالب الحالي
    projects = Project.query.filter_by(user_id=current_user.id).all()

    if not projects:
        flash('لا توجد مشاريع حتى الآن. يمكنك إضافة مشروع جديد.', 'info')

    return render_template('dashboard_student.html', projects=projects)

# لوحة تحكم المستثمر
@app.route('/dashboard_investor', methods=['GET'])
@login_required
def dashboard_investor():
    if current_user.role != 'investor':
        flash('ليس لديك إذن للوصول إلى هذه الصفحة!', 'danger')
        return redirect(url_for('home'))
    
    # البحث عن المشاريع بناءً على الاستعلامات
    search_query = request.args.get('search', '').strip()
    sector = request.args.get('sector', '')
    min_amount = request.args.get('min_amount', 0, type=float)
    max_amount = request.args.get('max_amount', None, type=float)

    query = Project.query

    if search_query:
        query = query.filter(or_(Project.title.contains(search_query), Project.description.contains(search_query)))
    if sector:
        query = query.filter_by(sector=sector)
    if min_amount:
        query = query.filter(Project.target_amount >= min_amount)
    if max_amount:
        query = query.filter(Project.target_amount <= max_amount)

    projects = query.all()

    if not projects:
        flash('لا توجد مشاريع تطابق معايير البحث.', 'info')

    return render_template('dashboard_investor.html', projects=projects)

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True)