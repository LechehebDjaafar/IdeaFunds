from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    target_amount = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))  # اختياري
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    student = db.relationship('Student', backref=db.backref('projects', lazy=True))