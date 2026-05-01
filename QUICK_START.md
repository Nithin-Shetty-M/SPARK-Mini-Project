# Quick Start Guide - Security Updates

## Installation & Setup (2 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
All required packages (Flask-Bcrypt, python-dotenv) are already listed.

### 2. Create Configuration
```bash
# Create .env file from template
cp .env.example .env

# Edit .env with your values (in your editor or terminal)
nano .env  # or use your favorite editor
```

### 3. Migrate Existing Passwords
If you have existing user data in your database:
```bash
python migrate_passwords.py
```

### 4. Run the Application
```bash
python app.py
```

---

## What's New?

### 🔐 Password Hashing
- Passwords are now hashed with bcrypt
- Old passwords automatically migrated
- Safer against database breaches

### 🔑 Environment Variables
- Sensitive config in `.env` file
- Not committed to git
- Easy to change between environments

### ⚡ Search Performance
- Database indexes added
- Faster searches on large datasets
- No code changes needed

---

## Testing the Changes

### Test Secure Login
1. Navigate to student/guide/admin login
2. Enter credentials
3. Should authenticate correctly with hashed passwords

### Test Environment Config
```python
# In Python shell:
import os
from dotenv import load_dotenv
load_dotenv()
print(os.getenv('SECRET_KEY'))  # Should print your secret key
```

### Test Search Performance
1. Go to Student Portal
2. Try searching for projects
3. Should be noticeably faster with larger datasets

---

## File Changes Summary

| File | Changes | Notes |
|------|---------|-------|
| `app.py` | Updated imports, models, routes | Password hashing + environment config |
| `.env` | 🆕 Created | Your local configuration (not in git) |
| `.env.example` | 🆕 Created | Template for new developers |
| `migrate_passwords.py` | 🆕 Created | Run once to hash existing passwords |
| `SECURITY_AND_PERFORMANCE_IMPROVEMENTS.md` | 🆕 Created | Detailed documentation |

---

## Before & After Comparison

### Before
```python
# app.py (insecure)
app.secret_key = "college_secret_key"  # Hardcoded!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'  # Hardcoded!

# Login route (plaintext comparison)
if Guide.query.filter_by(email=email, password=pw).first():
    # Password compared as plaintext!
    
# New guide creation
new_g = Guide(password=request.form['password'])  # Stored as plaintext!
```

### After
```python
# app.py (secure)
load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')  # From environment
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')  # From environment
bcrypt = Bcrypt(app)

# Login route (hashed comparison)
guide = Guide.query.filter_by(email=email).first()
if guide and guide.check_password(pw):
    # Password verified via bcrypt!
    
# New guide creation
new_g = Guide(email=request.form['email'])
new_g.set_password(request.form['password'])  # Hashed before storing!
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `.env: No such file or directory` | Run `cp .env.example .env` |
| `ModuleNotFoundError: dotenv` | Run `pip install python-dotenv` |
| Login doesn't work after update | Run `python migrate_passwords.py` |
| `Key 'SECRET_KEY' not found` | Edit `.env` and add missing keys |
| Searches still slow | Ensure `db.create_all()` was called |

---

## Next Steps

1. ✅ **Review changes** - Read `SECURITY_AND_PERFORMANCE_IMPROVEMENTS.md`
2. ✅ **Test locally** - Verify all logins work
3. ✅ **Update CI/CD** - Ensure `.env` is handled securely in deployment
4. ✅ **Deploy** - Push changes to production
5. ✅ **Monitor** - Check logs for any authentication issues

---

## Production Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Update `ADMIN_PASSWORD` to a secure password
- [ ] Store `.env` in your secret management system
- [ ] Ensure `.env` is NOT in version control
- [ ] Run `python migrate_passwords.py`
- [ ] Test all authentication flows
- [ ] Monitor application logs
- [ ] Plan database backup strategy

---

**Questions?** Refer to the full documentation in `SECURITY_AND_PERFORMANCE_IMPROVEMENTS.md`
