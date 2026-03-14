from flask import Flask, render_template, request, redirect, session, send_from_directory, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import pandas as pd
import uuid

app = Flask(__name__)
app.secret_key = "college_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False #for bulk students upload
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# --- Database Models ---

class Guide(db.Model):
    id = db.Column(db.Integer, primary_key=True)
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
    # course = db.Column(db.String(50))
    # academic_year = db.Column(db.String(10))
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
    __tablename__ = 'Student_login'
    roll_no = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100))
    course = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    batch = db.Column(db.String(20))

    def __repr__(self):
        return f'<Student {self.roll_no}: {self.name}>'

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
        
        if role == 'Admin' and email == 'admin@gmail.com' and pw == 'admin123':
            session['role'] = 'admin'
            return redirect('/admin/dashboard')
        
        elif role == 'Guide':
            g = Guide.query.filter_by(email=email, password=pw).first()
            if g:
                session['role'] = 'guide'
                session['user_id'] = g.id
                return redirect('/guide/dashboard')
        
        elif role == 'Student':
            s = Student_login.query.filter_by(email=email, password=pw).first()
            if s:
                session['role'] = 'student'
                return redirect('/student/dashboard')
        
        return "Invalid Credentials"
    return render_template('login.html',role=role)

# --- Admin Functions ---

@app.route('/admin/dashboard')
def admin_dash():
    guides = Guide.query.all()
    projects = Project.query.all()
    students= Student_login.query.all()
    return render_template('admin.html', guides=guides, projects=projects,students=students)

@app.route('/admin/add_guide')
def add_guide():
    return render_template('new_guide.html')

@app.route('/admin/add_students')
def add_students():
    return render_template('bulk_students.html')

@app.route('/admin/new_guide', methods=['POST'])
def new_guide():
    new_g = Guide(name=request.form['name'], email=request.form['email'], 
                  password=request.form['password'], department=request.form['dept'])
    db.session.add(new_g)
    db.session.commit()
    return redirect('/admin/dashboard')

@app.route('/admin/new_students', methods=['POST'])
def upload_csv_file():
    file = request.files.get('file')
    if not file or file.filename == '':
        return "No file selected", 400

    try:
        # 1. Read the CSV into a DataFrame
        df = pd.read_csv(file)

        # 2. Use SQLAlchemy engine to write the data
        # 'if_exists=append' works seamlessly with SQLAlchemy objects
        df.to_sql(
            'Student_login', 
            con=db.engine, 
            if_exists='append', 
            index=False
        )

        return redirect('/admin/dashboard')
        
        # return f"Successfully inserted {len(df)} rows using SQLAlchemy."

    except Exception as e:
        # pandas + sqlalchemy usually raises IntegrityError if PKs conflict
        return f"An error occurred: {str(e)}", 500

#--- Guide functions
@app.route('/guide/dashboard')
def guide_dash():
    g=session['user_id']
    return render_template("guide.html",g=g)

@app.route('/guide/new_project/<g>')
def new_project(g):
    return render_template("new_project.html",g=g)

@app.route('/guide/new_project/add/<G>', methods=['POST'])
def upload_file(G):
    g=Guide.query.filter_by(id=G).first()
    name=request.form['name']
    batch=request.form['batch']
    file = request.files.get('file')
    if file and file.filename != '':
        original_name = file.filename
        # Generate unique filename using UUID
        extension = os.path.splitext(original_name)[1]
        unique_name = f"{uuid.uuid4()}{extension}"
        
        # Save physical file
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file.save(filepath)
        
        # Save record to DB via ORM
        new_file = Project(name=name, stored_name=unique_name, batch=batch, guide_id=g.id)
        db.session.add(new_file)
        db.session.flush()
    #     db.session.commit()
        
    # return redirect(url_for('index'))
        p = Project.query.filter_by(stored_name=unique_name, guide_id=g.id).first()
        student_count = 0
        for i in range(1, 8):
            roll = request.form.get(f'roll_no_{i}')
            name = request.form.get(f'name_{i}')
            section = request.form.get(f'section_{i}')
            academic_year=request.form.get('academic_year')
            course=request.form.get(f'course_{i}')

            # Only create an entry if Roll Number is provided
            if roll and roll.strip():
                new_student = Student(
                    roll_no=roll,
                    academic_year=academic_year,
                    name=name,
                    course=course,
                    section=section,
                    project_id=p.id  # Link to the project we just created
                )
                db.session.add(new_student)
                student_count += 1

        # 4. Final Validation & Commit
        if student_count < 3:
            db.session.rollback()
            return "Error: You must provide at least 3 students."

        db.session.commit()
        return redirect('/guide/dashboard')

    return "File missing", 400


# --- Student Functions ---

@app.route('/student/dashboard')
def student_dash():
    search = request.args.get('search')
    dept = request.args.get('dept')
    query = Project.query.all()
    
    if search: query = query.filter(Project.name.contains(search))
    if dept: query = query.join(Guide).filter(Guide.department.contains(dept))
    
    return render_template('student.html', projects=query)
    

# Main loop
if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    with app.app_context():
        db.create_all()
    app.run(debug=True)