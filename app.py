from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

# إنشاء تطبيق Flask
app = Flask(__name__)

# إعداد قاعدة البيانات
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projects.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# إنشاء مثيل لـ SQLAlchemy
db = SQLAlchemy(app)

# نموذج الطالب
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# نموذج المشروع
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))  # اختياري
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    student = db.relationship('Student', backref=db.backref('projects', lazy=True))

# رابط لعرض المشاريع
@app.route('/projects')
def projects():
    all_projects = Project.query.all()
    return render_template('projects.html', projects=all_projects)

# رابط لإضافة مشروع جديد
@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        target_amount = float(request.form['target_amount'])
        image_url = request.form.get('image_url', '')  # اختياري
        student_id = 1  # افترض أن الطالب ID=1 (يمكن تعديل ذلك لاحقًا)
        
        new_project = Project(
            title=title,
            description=description,
            target_amount=target_amount,
            image_url=image_url,
            student_id=student_id
        )
        db.session.add(new_project)
        db.session.commit()
        return redirect(url_for('projects'))
    
    return render_template('add_project.html')

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True)