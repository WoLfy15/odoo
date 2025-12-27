# GearGuard Authentication System

## Overview
Complete user authentication system with login, signup, and session management.

## Features

### 1. User Registration (Sign Up)
- **URL**: `/signup`
- **Fields**:
  - Full Name (min 2 characters)
  - Username (min 3 characters, alphanumeric + underscore only)
  - Email (valid email format, must be unique)
  - Password (min 8 chars, must include uppercase, lowercase, number, special character)
  - Confirm Password (must match password)
- **Validation**: Real-time client-side + server-side validation
- **Security**: Passwords are hashed using werkzeug's generate_password_hash

### 2. User Login
- **URL**: `/login`
- **Fields**:
  - Email
  - Password
- **Features**:
  - Secure password verification using check_password_hash
  - Last login timestamp tracking
  - Session creation with user details

### 3. Session Management
- User information stored in session:
  - user_id
  - username
  - name
  - email
  - role
- Session persists across requests
- Navbar shows logged-in user's name and role

### 4. Logout
- **URL**: `/logout`
- Clears all session data
- Redirects to login page

## Database Schema

### User Model
```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
```

## Password Requirements
- Minimum 8 characters
- At least one uppercase letter (A-Z)
- At least one lowercase letter (a-z)
- At least one number (0-9)
- At least one special character (!@#$%^&*(),.?":{}|<>)

## UI/UX Features
- Modern gradient design (purple theme)
- Animated slide-up effect on page load
- Real-time validation feedback
- Visual password requirement checklist
- Hover effects on buttons
- Responsive design
- Error/success message display

## Security Features
1. **Password Hashing**: Using werkzeug's pbkdf2:sha256
2. **Input Validation**: Both client and server-side
3. **Email Uniqueness**: Prevents duplicate accounts
4. **Username Uniqueness**: Prevents duplicate usernames
5. **Session Security**: Uses Flask's secure session with SECRET_KEY
6. **SQL Injection Protection**: Using SQLAlchemy ORM

## Usage

### Creating a New Account
1. Navigate to `/signup` or click "Sign Up" from login page
2. Fill in all required fields
3. Ensure password meets all requirements (checkmarks will appear)
4. Click "Sign Up"
5. Auto-login after successful registration

### Logging In
1. Navigate to `/login`
2. Enter registered email and password
3. Click "Sign In"
4. Redirects to dashboard upon success

### Accessing Protected Pages
Currently, all pages are accessible without login. To protect pages:

```python
from app import login_required

@app.route('/protected-page')
@login_required
def protected_page():
    return render_template('protected.html')
```

## API Routes

| Route | Method | Description | Authentication Required |
|-------|--------|-------------|------------------------|
| `/login` | GET, POST | Login page and authentication | No |
| `/signup` | GET, POST | Registration page and user creation | No |
| `/logout` | GET | Logout and session clearing | No |
| All other routes | GET, POST | Application features | Optional (can be added) |

## Future Enhancements
- [ ] Email verification
- [ ] Password reset functionality
- [ ] "Remember Me" feature
- [ ] Two-factor authentication
- [ ] User profile management
- [ ] Role-based access control
- [ ] Password strength meter
- [ ] Account lockout after failed attempts
- [ ] Activity logging

## Testing

### Test Account Creation
1. Go to `http://localhost:5000/signup`
2. Create test account:
   - Name: Test User
   - Username: testuser
   - Email: test@example.com
   - Password: Test@1234
   - Confirm Password: Test@1234

### Test Login
1. Go to `http://localhost:5000/login`
2. Login with created account
3. Verify user info appears in navbar
4. Check that "Logout" button is visible

## Files Modified/Created

### New Files
- `gear_guard/templates/login.html` - Login page
- `gear_guard/templates/signup.html` - Registration page

### Modified Files
- `gear_guard/app.py` - Added auth routes and login_required decorator
- `gear_guard/models.py` - Enhanced User model with password hashing
- `gear_guard/templates/base.html` - Added user menu and logout button

## Dependencies
- Flask
- Flask-SQLAlchemy
- Werkzeug (for password hashing)

## Configuration
- SECRET_KEY: Set in `config.py` (change for production)
- Session Type: Server-side (Flask default)
- Database: SQLite (`database.db`)
