"""
Migration Script: Hash Existing Passwords
==========================================
This script hashes all plain-text passwords in the database.
Use this if you have an existing database with plain-text passwords.

Run this script ONCE before deploying the updated app:
    python migrate_passwords.py
"""

import os
import sys
from dotenv import load_dotenv
from flask_bcrypt import Bcrypt
from app import app, db, Guide, Student_login

load_dotenv()

bcrypt = Bcrypt(app)

def migrate_passwords():
    """Hash all plain-text passwords in the database"""
    print("Starting password migration...")
    
    with app.app_context():
        # Migrate Guide passwords
        guides = Guide.query.all()
        guides_migrated = 0
        
        for guide in guides:
            # Skip if already hashed (bcrypt hashes start with $2b$, $2a$, or $2y$)
            if guide.password and not guide.password.startswith('$2'):
                print(f"Hashing password for Guide: {guide.email}")
                guide.set_password(guide.password)
                guides_migrated += 1
        
        if guides_migrated > 0:
            db.session.commit()
            print(f"✓ Migrated {guides_migrated} Guide passwords")
        else:
            print("✓ All Guide passwords already hashed")
        
        # Migrate Student_login passwords
        students = Student_login.query.all()
        students_migrated = 0
        
        for student in students:
            # Skip if already hashed (bcrypt hashes start with $2b$, $2a$, or $2y$)
            if student.password and not student.password.startswith('$2'):
                print(f"Hashing password for Student: {student.roll_no}")
                student.set_password(student.password)
                students_migrated += 1
        
        if students_migrated > 0:
            db.session.commit()
            print(f"✓ Migrated {students_migrated} Student passwords")
        else:
            print("✓ All Student passwords already hashed")
        
        print("\n✓ Password migration completed successfully!")
        print("You can now run the updated Flask app with secure password hashing.")

if __name__ == '__main__':
    try:
        migrate_passwords()
    except Exception as e:
        print(f"✗ Migration failed: {str(e)}")
        sys.exit(1)
