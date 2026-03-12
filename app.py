from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "college_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# --- Database Models ---

class Guide(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    department = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    projects = db.relationship('Project', backref='guide', lazy=True)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    stored_name = db.Column(db.String(200))
    submission_date = db.Column(db.DateTime, default=datetime.utcnow)
    # student_reg_nos = db.Column(db.Text)
    course = db.Column(db.String(50))
    academic_year = db.Column(db.String(10))
    batch = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Pending')
    rejection_reason = db.Column(db.Text, nullable=True)
    guide_id = db.Column(db.String(50), db.ForeignKey('guide.id'))
    students= db.relationship('Student',backref='project',lazy=True)


class Student(db.Model):
    roll_no = db.Column(db.String(50), primary_key=True)
    academic_year= db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100))
    course = db.Column(db.String(20))
    section= db.Column(db.String(5))
    project_id = db.Column(db.String(50), db.ForeignKey('project.id'))


class Student_login(db.Model):
    roll_no = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100))
    course = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    batch = db.Column(db.String(20))

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

# Basic Login Router
@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    if request.method == 'POST':
        email = request.form.get('email')
        pw = request.form.get('password')
        
        if role == 'admin' and email == 'admin@gmail.com' and pw == 'admin123':
            session['role'] = 'admin'
            return redirect('/admin/dashboard')
        
        elif role == 'guide':
            g = Guide.query.filter_by(email=email, password=pw).first()
            if g:
                session['role'] = 'guide'
                session['user_id'] = g.id
                return redirect('/guide/dashboard')
        
        elif role == 'student':
            s = Student.query.filter_by(email=email, password=pw).first()
            if s:
                session['role'] = 'student'
                return redirect('/student/dashboard')
        
        return "Invalid Credentials"
    return render_template('login.html',role=role)



# Main loop
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    with app.app_context():
        db.create_all()
    app.run(debug=True)