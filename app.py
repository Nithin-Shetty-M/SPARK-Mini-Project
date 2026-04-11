from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for, Response
import flask.json
import os
import pandas as pd
import uuid
import io
import csv
from datetime import datetime

# --- FLASK 3.0+ COMPATIBILITY PATCH START ---
# This fixes: "ImportError: cannot import name 'JSONEncoder' from 'flask.json'"
# and "AttributeError: 'Flask' object has no attribute 'json_encoder'"
try:
    from flask.json import JSONEncoder
except ImportError:
    import json
    class JSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if hasattr(obj, '__iter__'):
                return list(obj)
            return super().default(obj)
    flask.json.JSONEncoder = JSONEncoder
# --- FLASK 3.0+ COMPATIBILITY PATCH END ---

from flask_mongoengine import MongoEngine

app = Flask(__name__)
app.secret_key = "college_secret_key"

# Apply the patch to the app instance
app.json_encoder = JSONEncoder

# --- MongoDB Configuration ---
app.config['MONGODB_SETTINGS'] = {
    'db': 'college_db',
    'host': 'localhost',
    'port': 27017
}
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = MongoEngine(app)

# --- MongoDB Documents (Models) ---

class Guide(db.Document):
    name = db.StringField(max_length=100)
    email = db.StringField(max_length=100, unique=True)
    password = db.StringField(max_length=100)
    department = db.StringField(max_length=50)
    is_active = db.BooleanField(default=True)

class Department(db.Document):
    name = db.StringField(max_length=100, unique=True, required=True)

class Student(db.EmbeddedDocument):
    roll_no = db.StringField(max_length=50)
    academic_year = db.StringField(max_length=10)
    name = db.StringField(max_length=100)
    course = db.StringField(max_length=20)
    section = db.StringField(max_length=5)

class Project(db.Document):
    name = db.StringField(max_length=200)
    stored_name = db.StringField(max_length=200)
    submission_date = db.DateTimeField(default=datetime.utcnow)
    batch = db.StringField(max_length=20)
    status = db.StringField(default='Pending')
    rejection_reason = db.StringField()
    guide = db.ReferenceField(Guide)
    students = db.ListField(db.EmbeddedDocumentField(Student))

class StudentLogin(db.Document):
    meta = {'collection': 'student_login'}
    roll_no = db.StringField(primary_key=True) 
    name = db.StringField(max_length=100)
    course = db.StringField(max_length=100)
    email = db.StringField(max_length=100)
    password = db.StringField(max_length=100)
    batch = db.StringField(max_length=20)

# --- Routes ---

@app.route('/')
def index():
    guides = Guide.objects.all()
    projects = Project.objects.all()
    departments = Department.objects.all()
    return render_template('index.html', guides=guides, projects=projects, departments=departments)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/login/<role>', methods=['GET', 'POST']) 
def login(role):
    if request.method == 'POST':
        email = request.form.get('email')
        pw = request.form.get('password')
        
        if role == 'Admin' and email == 'admin@gmail.com' and pw == 'admin123':
            session['role'] = 'admin'
            return redirect('/admin/dashboard')
        
        elif role == 'Guide':
            g = Guide.objects(email=email, password=pw).first()
            if g:
                session['role'] = 'guide'
                session['user_id'] = str(g.id)
                return redirect('/guide/dashboard')
        
        elif role == 'Student':
            s = StudentLogin.objects(email=email, password=pw).first()
            if s:
                session['role'] = 'student'
                session['student_rono'] = s.roll_no
                return redirect('/student/dashboard')
        
        return "Invalid Credentials"
    return render_template('login.html', role=role)

# --- Admin Functions ---

@app.route('/admin/dashboard')
def admin_dash():
    if session.get('role') != 'admin':
        return "Unauthorized", 401
    guides = Guide.objects.all()
    projects = Project.objects.all()
    students = StudentLogin.objects.all()
    departments = Department.objects.order_by('name')
    return render_template('admin.html', guides=guides, projects=projects, students=students, departments=departments)

@app.route('/admin/new_department', methods=['POST'])
def new_department():
    name = request.form.get('name', '').strip()
    if name and not Department.objects(name__iexact=name).first():
        Department(name=name).save()
    return redirect('/admin/dashboard')

@app.route('/admin/new_guide', methods=['POST'])
def new_guide():
    Guide(
        name=request.form['name'], 
        email=request.form['email'], 
        password=request.form['password'], 
        department=request.form['dept']
    ).save()
    return redirect('/admin/dashboard')

@app.route('/admin/new_students', methods=['POST'])
def upload_csv_file():
    file = request.files.get('file')
    if not file: return "No file", 400
    try:
        df = pd.read_csv(file)
        # MongoDB Insert
        records = [StudentLogin(**row) for row in df.to_dict('records')]
        StudentLogin.objects.insert(records)
        return redirect('/admin/dashboard')
    except Exception as e:
        return f"Error: {e}", 500

@app.route('/admin/add_guide')
def add_guide():
    if session.get('role') != 'admin':
        return "Unauthorized", 401
    departments = Department.objects.order_by('name')
    return render_template('new_guide.html', departments=departments)

@app.route('/admin/add_students')
def add_students():
    if session.get('role') != 'admin':
        return "Unauthorized", 401
    return render_template('bulk_students.html')

@app.route('/admin/toggle_guide/<id>')
def toggle_guide(id):
    if session.get('role') != 'admin':
        return "Unauthorized", 401
    g = Guide.objects.get_or_404(id=id)
    g.is_active = not g.is_active
    g.save()
    return redirect('/admin/dashboard')

@app.route('/admin/download_template')
def download_template():
    if session.get('role') != 'admin':
        return "Unauthorized", 401
    # Define the exact column headers the MongoDB StudentLogin model expects
    column_headers = ['roll_no', 'name', 'course', 'email', 'password', 'batch']
    
    dest = io.StringIO()
    writer = csv.writer(dest)
    writer.writerow(column_headers)
    
    output = dest.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=student_template.csv"}
    )

# --- Guide Functions ---

# @app.route('/guide/dashboard')
# def guide_dash():
#     if session.get('role') != 'guide':
#         return "Unauthorized", 401
#     g_id = session['user_id']
#     return render_template("guide.html", g=g_id, guide=Guide.objects.get(id=g_id))

@app.route('/guide/dashboard')
def guide_dash():
    if session.get('role') != 'guide':
        return "Unauthorized", 401
    
    g_id = session['user_id']
    current_guide = Guide.objects.get(id=g_id)
    
    # NEW: Fetch projects belonging to THIS guide specifically
    guide_projects = Project.objects(guide=current_guide) 
    
    return render_template("guide.html", g=g_id, guide=current_guide, projects=guide_projects)

@app.route('/guide/new_project/add/<G>', methods=['POST'])
def upload_file(G):
    guide = Guide.objects.get(id=G)
    file = request.files.get('file')
    if not file: return "File missing", 400

    unique_name = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
    
    new_project = Project(
        name=request.form['name'],
        stored_name=unique_name,
        batch=request.form['batch'],
        guide=guide
    )

    student_list = []
    for i in range(1, 8):
        roll = request.form.get(f'roll_no_{i}')
        if roll and roll.strip():
            student_list.append(Student(
                roll_no=roll,
                name=request.form.get(f'name_{i}'),
                section=request.form.get(f'section_{i}'),
                academic_year=request.form.get('academic_year'),
                course=request.form.get(f'course_{i}')
            ))

    if len(student_list) < 3:
        return "Error: At least 3 students required", 400

    new_project.students = student_list
    new_project.save()
    return redirect('/guide/dashboard')

@app.route('/delete_project/<pid>')
def delete_project(pid):
    project = Project.objects.get_or_404(id=pid)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], project.stored_name)
    if os.path.exists(file_path):
        os.remove(file_path)
    project.delete()
    return redirect("/guide/dashboard")

@app.route('/guide/new_project/<g>')
def new_project(g):
    if session.get('role') != 'guide':
        return "Unauthorized", 401
    return render_template("new_project.html", g=g)

# --- Student Functions ---

@app.route('/student/dashboard')
def student_dash():
    if session.get('role') != 'student':
        return "Unauthorized", 401
    
    student = StudentLogin.objects.get(roll_no=session['student_rono'])
    search = request.args.get('psearch')
    dept = request.args.get('pdept')
    
    query_params = {}
    if search: query_params['name__icontains'] = search
    
    projects = Project.objects(**query_params)
    
    if dept:
        projects = [p for p in projects if dept.lower() in p.guide.department.lower()]

    guides = Guide.objects.all()
    for guide in guides:
        guide.project_count = Project.objects(guide=guide).count()

    return render_template('student.html', projects=projects, guides=guides, student=student)

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename) 

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True)