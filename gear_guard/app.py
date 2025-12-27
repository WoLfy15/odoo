from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_migrate import Migrate
from config import Config
from extensions import db
from models import *
from datetime import datetime
import re
import os
from functools import wraps

app = Flask(__name__)
app.config.from_object(Config)

# Add secret key for sessions
if not app.config.get('SECRET_KEY'):
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

db.init_app(app)
migrate = Migrate(app, db)

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        # Validate inputs
        if not email or not password:
            return render_template('login.html', error='Email and password are required')
        
        # Check if user exists
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Login successful
            session['user_id'] = user.id
            session['username'] = user.username
            session['name'] = user.name
            session['email'] = user.email
            session['role'] = user.role
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid email or password')
    
    # GET request - show login form
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirmPassword', '')
        
        # Validate inputs
        errors = []
        
        if not name or len(name) < 2:
            errors.append('Name must be at least 2 characters')
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Username can only contain letters, numbers, and underscores')
        
        if not email or not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append('Please enter a valid email address')
        
        if not password or len(password) < 8:
            errors.append('Password must be at least 8 characters')
        elif not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        elif not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        elif not re.search(r'[0-9]', password):
            errors.append('Password must contain at least one number')
        elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append('Password must contain at least one special character')
        
        if password != confirm_password:
            errors.append('Passwords do not match')
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered')
        
        if errors:
            return render_template('signup.html', error=' | '.join(errors))
        
        # Create new user
        try:
            new_user = User(
                name=name,
                username=username,
                email=email,
                role='user'
            )
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            # Auto login after signup
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session['name'] = new_user.name
            session['email'] = new_user.email
            session['role'] = new_user.role
            
            flash('Account created successfully!', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            return render_template('signup.html', error=f'Error creating account: {str(e)}')
    
    # GET request - show signup form
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

# Helper: generate next employee code like EMP0001
def generate_employee_id():
    existing_rows = TeamMember.query.with_entities(TeamMember.employee_id)\
        .filter(TeamMember.employee_id.isnot(None)).all()
    existing_ids = [row[0] for row in existing_rows if row and row[0]]
    numbers = []
    for eid in existing_ids:
        m = re.fullmatch(r"EMP(\d+)", eid.strip())
        if m:
            numbers.append(int(m.group(1)))
    next_n = (max(numbers) + 1) if numbers else 1
    candidate = f"EMP{next_n:04d}"
    # ensure uniqueness even if non-standard codes exist
    while TeamMember.query.filter_by(employee_id=candidate).first():
        next_n += 1
        candidate = f"EMP{next_n:04d}"
    return candidate

@app.route('/')
def dashboard():
    # Get statistics for dashboard
    total_teams = Team.query.count()
    total_members = TeamMember.query.count()
    total_equipment = Equipment.query.count()
    active_members = TeamMember.query.filter_by(status='active').count()
    
    # Get all requests for the table (with safe column access)
    try:
        all_requests = Request.query.order_by(Request.created_at.desc()).limit(10).all()
        pending_requests = Request.query.filter_by(status='NEW_REQUEST').count()
        
        # Count requests by type
        corrective_requests = Request.query.filter_by(type='CORRECTIVE').count()
        preventive_requests = Request.query.filter_by(type='PREVENTIVE').count()
        
        # Get overdue requests (due_date passed but status still pending)
        from datetime import date
        overdue_requests = Request.query.filter(
            Request.due_date < date.today(),
            Request.status.in_(['NEW_REQUEST', 'IN_PROGRESS'])
        ).count()
    except Exception as e:
        print(f"Error fetching requests: {e}")
        all_requests = []
        pending_requests = 0
        corrective_requests = 0
        preventive_requests = 0
        overdue_requests = 0
    
    # Calculate critical equipment (status = 'critical' or 'maintenance')
    try:
        critical_equipment = Equipment.query.filter(
            Equipment.status.in_(['critical', 'maintenance', 'under_repair'])
        ).count()
    except:
        critical_equipment = 0
    
    # Get equipment by status
    try:
        available_equipment = Equipment.query.filter_by(status='available').count()
        in_use_equipment = Equipment.query.filter_by(status='in_use').count()
    except:
        available_equipment = 0
        in_use_equipment = 0
    
    # Calculate technician load (active members vs pending requests)
    tech_load = min(int((pending_requests / max(active_members, 1)) * 100), 100) if active_members > 0 else 0
    
    # Get recent teams
    recent_teams = Team.query.order_by(Team.id.desc()).limit(5).all()
    
    # Get technicians for quick access
    technicians = TeamMember.query.filter_by(status='active').order_by(TeamMember.name).all()
    
    return render_template('dashboard.html', 
                         total_teams=total_teams,
                         total_members=total_members,
                         total_equipment=total_equipment,
                         active_members=active_members,
                         critical_equipment=critical_equipment,
                         tech_load=tech_load,
                         pending_requests=pending_requests,
                         overdue_requests=overdue_requests,
                         corrective_requests=corrective_requests,
                         preventive_requests=preventive_requests,
                         available_equipment=available_equipment,
                         in_use_equipment=in_use_equipment,
                         all_requests=all_requests,
                         recent_teams=recent_teams,
                         technicians=technicians)

@app.route('/equipment')
def equipment():
    all_equipment = Equipment.query.all()
    # Build maps for related display (team and member names)
    teams_by_id = {t.id: t for t in Team.query.all()}
    members_by_id = {m.id: m for m in TeamMember.query.all()}
    return render_template('equipment.html', equipment=all_equipment, teams_by_id=teams_by_id, members_by_id=members_by_id)

# Removed Requests form route

@app.route('/kanban')
def kanban():
    # Fetch tasks (requests) from DB
    tasks = []
    try:
        for r in Request.query.all():
            tasks.append({
                'id': r.id,
                'title': r.title,
                'status': r.status or 'NEW',
                'type': getattr(r, 'type', None) or 'CORRECTIVE',
                'dueDate': r.due_date.strftime('%Y-%m-%d') if r.due_date else None,
            })
    except:
        pass
    return render_template('kanban.html', tasks=tasks)

@app.route('/kanban/move', methods=['POST'])
def kanban_move():
    data = request.get_json(silent=True) or {}
    task_id = data.get('taskId')
    new_status = data.get('newStatus')
    if not task_id or not new_status:
        return {'ok': False, 'error': 'Missing taskId or newStatus'}, 400
    req = Request.query.get(task_id)
    if not req:
        return {'ok': False, 'error': 'Task not found'}, 404
    req.status = new_status
    req.updated_at = datetime.utcnow()
    db.session.commit()
    return {'ok': True}

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

@app.route('/requests')
def requests():
    all_requests = Request.query.order_by(Request.created_at.desc()).all()
    return render_template('requests.html', requests=all_requests)

# Team Management Routes
@app.route('/teams')
def teams():
    all_teams = Team.query.all()
    return render_template('teams.html', teams=all_teams)

@app.route('/teams/add', methods=['GET', 'POST'])
def add_team():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        department = request.form.get('department')
        company = request.form.get('company')
        
        new_team = Team(name=name, description=description, department=department, company=company)
        db.session.add(new_team)
        db.session.commit()
        flash('Team added successfully!', 'success')
        return redirect(url_for('teams'))
    
    return render_template('add_team.html')

@app.route('/teams/<int:team_id>')
def team_detail(team_id):
    team = Team.query.get_or_404(team_id)
    members = TeamMember.query.filter_by(team_id=team_id).all()
    return render_template('team_detail.html', team=team, members=members)

@app.route('/teams/<int:team_id>/edit', methods=['GET', 'POST'])
def edit_team(team_id):
    team = Team.query.get_or_404(team_id)
    if request.method == 'POST':
        team.name = request.form.get('name')
        team.description = request.form.get('description')
        team.department = request.form.get('department')
        team.company = request.form.get('company')
        team.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Team updated successfully!', 'success')
        return redirect(url_for('team_detail', team_id=team_id))
    
    return render_template('edit_team.html', team=team)

@app.route('/teams/<int:team_id>/delete', methods=['POST'])
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    db.session.delete(team)
    db.session.commit()
    flash('Team deleted successfully!', 'success')
    return redirect(url_for('teams'))

# Team Member Routes
@app.route('/members')
def members():
    all_members = TeamMember.query.all()
    return render_template('members.html', members=all_members)

@app.route('/members/add', methods=['GET', 'POST'])
def add_member():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        position = request.form.get('position')
        team_id = request.form.get('team_id')
        joining_date_str = request.form.get('joining_date')
        action = request.form.get('action', 'done')
        
        joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date() if joining_date_str else None

        # Field-level validations
        field_errors = {}
        if not name:
            field_errors['name'] = 'Name is required.'
        if not email:
            field_errors['email'] = 'Email is required.'
        elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            field_errors['email'] = 'Enter a valid email address.'
        if not team_id:
            field_errors['team_id'] = 'Team selection is required.'
        if phone and not re.fullmatch(r"\d{10}", phone):
            field_errors['phone'] = 'Phone number must be exactly 10 digits.'

        # Duplicate checks
        if email and TeamMember.query.filter_by(email=email).first():
            field_errors['email'] = 'Email already exists. Please use a unique email.'
        if phone and TeamMember.query.filter_by(phone=phone).first():
            field_errors['phone'] = 'Phone number already exists. Please use a unique phone number.'
        if name and TeamMember.query.filter_by(name=name).first():
            field_errors['name'] = 'A member with the same name already exists.'

        if field_errors:
            teams = Team.query.all()
            form_data = {
                'name': name,
                'email': email,
                'phone': phone,
                'position': position,
                'team_id': team_id,
                'employee_id': '',
                'joining_date': joining_date_str or ''
            }
            return render_template('add_member.html', teams=teams, form_data=form_data, field_errors=field_errors)

        # Always auto-assign employee code from database using generator
        employee_id = generate_employee_id()

        new_member = TeamMember(
            name=name,
            email=email,
            phone=phone,
            position=position,
            team_id=team_id,
            employee_id=employee_id,
            joining_date=joining_date
        )
        db.session.add(new_member)
        db.session.commit()
        flash('Team member added successfully!', 'success')
        
        # After add, always go to Teams dashboard
        return redirect(url_for('teams'))
    
    teams = Team.query.all()
    # Provide next employee id preview for the form (read-only)
    next_employee_id = generate_employee_id()
    return render_template('add_member.html', teams=teams, next_employee_id=next_employee_id)

@app.route('/members/<int:member_id>')
def member_detail(member_id):
    member = TeamMember.query.get_or_404(member_id)
    return render_template('member_detail.html', member=member)

@app.route('/members/<int:member_id>/edit', methods=['GET', 'POST'])
def edit_member(member_id):
    member = TeamMember.query.get_or_404(member_id)
    if request.method == 'POST':
        member.name = request.form.get('name')
        member.email = request.form.get('email')
        member.phone = request.form.get('phone')
        member.position = request.form.get('position')
        member.team_id = request.form.get('team_id')
        member.employee_id = request.form.get('employee_id')
        member.status = request.form.get('status')
        joining_date_str = request.form.get('joining_date')
        member.joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date() if joining_date_str else None

        # Field-level validations and duplicate checks (excluding current member)
        field_errors = {}
        if member.phone and not re.fullmatch(r"\d{10}", member.phone):
            field_errors['phone'] = 'Phone number must be exactly 10 digits.'
        if member.employee_id:
            existing_emp = TeamMember.query.filter(TeamMember.employee_id == member.employee_id, TeamMember.id != member.id).first()
            if existing_emp:
                field_errors['employee_id'] = 'Employee ID already exists. Please use a unique code.'
        existing_email = TeamMember.query.filter(TeamMember.email == member.email, TeamMember.id != member.id).first()
        if existing_email:
            field_errors['email'] = 'Email already exists. Please use a unique email.'
        elif member.email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", member.email):
            field_errors['email'] = 'Enter a valid email address.'
        if member.phone:
            existing_phone = TeamMember.query.filter(TeamMember.phone == member.phone, TeamMember.id != member.id).first()
            if existing_phone:
                field_errors['phone'] = 'Phone number already exists. Please use a unique phone number.'
        existing_name = TeamMember.query.filter(TeamMember.name == member.name, TeamMember.id != member.id).first()
        if existing_name:
            field_errors['name'] = 'A member with the same name already exists.'

        if field_errors:
            teams = Team.query.all()
            return render_template('edit_member.html', member=member, teams=teams, field_errors=field_errors)

        # Auto-assign employee code if missing using generator
        if not member.employee_id:
            member.employee_id = generate_employee_id()

        member.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Team member updated successfully!', 'success')
        return redirect(url_for('teams'))
    
    teams = Team.query.all()
    return render_template('edit_member.html', member=member, teams=teams)

@app.route('/members/<int:member_id>/delete', methods=['POST'])
def delete_member(member_id):
    member = TeamMember.query.get_or_404(member_id)
    db.session.delete(member)
    db.session.commit()
    flash('Team member deleted successfully!', 'success')
    return redirect(url_for('members'))

# Equipment Routes
@app.route('/equipment/add', methods=['GET', 'POST'])
def add_equipment():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        company = request.form.get('company', '').strip()
        description = request.form.get('description', '').strip()
        
        # Get IDs from form
        maintenance_team_id = request.form.get('maintenance_team_id', '')
        employee_id = request.form.get('employee_id', '')
        
        # Get dates
        assigned_date_str = request.form.get('assigned_date', '')
        scrap_date_str = request.form.get('scrap_date', '')
        
        # Get other fields
        used_in_location = request.form.get('used_in_location', '').strip()
        work_center = request.form.get('work_center', '').strip()
        
        # Convert to int or None
        def to_int_or_none(val):
            if val:
                try:
                    return int(val)
                except (ValueError, TypeError):
                    return None
            return None
        
        maintenance_team_id_int = to_int_or_none(maintenance_team_id)
        employee_id_int = to_int_or_none(employee_id)
        
        # Convert dates
        from datetime import datetime as dt
        assigned_date = dt.strptime(assigned_date_str, '%Y-%m-%d').date() if assigned_date_str else None
        scrap_date = dt.strptime(scrap_date_str, '%Y-%m-%d').date() if scrap_date_str else None
        
        # Validations
        errors = []
        if not name:
            errors.append('Equipment name is required.')
        
        existing_equipment = Equipment.query.filter_by(name=name).first()
        if existing_equipment:
            errors.append('Equipment with this name already exists.')
        
        if errors:
            for e in errors:
                flash(e, 'danger')
            team_members = TeamMember.query.all()
            teams = Team.query.all()
            companies = db.session.query(Team.company).distinct().filter(Team.company.isnot(None), Team.company != '').all()
            companies = [comp[0] for comp in companies]
            form_data = {
                'name': name,
                'category': category,
                'company': company,
                'description': description,
                'maintenance_team_id': maintenance_team_id,
                'employee_id': employee_id,
                'assigned_date': assigned_date_str,
                'scrap_date': scrap_date_str,
                'used_in_location': used_in_location,
                'work_center': work_center
            }
            return render_template('add_equipment.html', team_members=team_members, teams=teams, companies=companies, form_data=form_data)
        
        # Create new equipment
        new_equipment = Equipment(
            name=name,
            category=category,
            company=company,
            description=description,
            maintenance_team_id=maintenance_team_id_int,
            employee_id=employee_id_int,
            assigned_date=assigned_date,
            scrap_date=scrap_date,
            used_in_location=used_in_location,
            work_center=work_center,
            status='active',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_equipment)
        db.session.commit()
        flash('Equipment added successfully!', 'success')
        return redirect(url_for('equipment'))
    
    team_members = TeamMember.query.all()
    teams = Team.query.all()
    
    # Get unique companies from teams
    companies = db.session.query(Team.company).distinct().filter(Team.company.isnot(None), Team.company != '').all()
    companies = [comp[0] for comp in companies]  # Convert to list of strings
    
    return render_template('add_equipment.html', team_members=team_members, teams=teams, companies=companies)

@app.route('/equipment/view/<int:id>')
def view_equipment(id):
    equipment_item = Equipment.query.get_or_404(id)
    return render_template('view_equipment.html', equipment=equipment_item)

@app.route('/equipment/edit/<int:id>', methods=['GET', 'POST'])
def edit_equipment(id):
    equipment_item = Equipment.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        company = request.form.get('company', '').strip()
        maintenance_team_id = request.form.get('maintenance_team_id', '')
        assigned_date = request.form.get('assigned_date', '').strip()
        employee_id = request.form.get('employee_id', '')
        scrap_date = request.form.get('scrap_date', '').strip()
        work_center = request.form.get('work_center', '').strip()
        description = request.form.get('description', '').strip()
        
        # Convert IDs to int if not empty
        maintenance_team_id_int = int(maintenance_team_id) if maintenance_team_id else None
        employee_id_int = int(employee_id) if employee_id else None
        
        # Parse dates
        assigned_date = assigned_date if assigned_date else None
        scrap_date = scrap_date if scrap_date else None
        
        # Validations
        errors = []
        if not name:
            errors.append('Equipment name is required.')
        
        # Check for duplicate name (excluding current equipment)
        existing_equipment = Equipment.query.filter(
            Equipment.name == name,
            Equipment.id != id
        ).first()
        if existing_equipment:
            errors.append('Equipment with this name already exists.')
        
        if errors:
            for e in errors:
                flash(e, 'danger')
            team_members = TeamMember.query.all()
            teams = Team.query.all()
            companies = db.session.query(Team.company).distinct().filter(Team.company.isnot(None), Team.company != '').all()
            companies = [comp[0] for comp in companies]
            return render_template('edit_equipment.html', equipment=equipment_item, team_members=team_members, teams=teams, companies=companies)
        
        # Update equipment
        equipment_item.name = name
        equipment_item.category = category
        equipment_item.company = company
        equipment_item.maintenance_team_id = maintenance_team_id_int
        equipment_item.assigned_date = assigned_date
        equipment_item.employee_id = employee_id_int
        equipment_item.scrap_date = scrap_date
        equipment_item.work_center = work_center
        equipment_item.description = description
        equipment_item.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Equipment updated successfully!', 'success')
        return redirect(url_for('equipment'))
    
    team_members = TeamMember.query.all()
    teams = Team.query.all()
    
    # Get unique companies from teams
    companies = db.session.query(Team.company).distinct().filter(Team.company.isnot(None), Team.company != '').all()
    companies = [comp[0] for comp in companies]
    
    return render_template('edit_equipment.html', equipment=equipment_item, team_members=team_members, teams=teams, companies=companies)

@app.route('/equipment/delete/<int:id>', methods=['POST'])
def delete_equipment(id):
    equipment_item = Equipment.query.get_or_404(id)
    db.session.delete(equipment_item)
    db.session.commit()
    flash('Equipment deleted successfully!', 'success')
    return redirect(url_for('equipment'))

@app.route('/equipment/<int:equipment_id>/maintenance')
def equipment_maintenance(equipment_id):
    """Smart button route - shows maintenance requests for specific equipment"""
    equipment_item = Equipment.query.get_or_404(equipment_id)
    # Get all requests related to this equipment
    # For now, we'll return a simple page showing equipment maintenance requests
    maintenance_requests = []  # Would filter by equipment_id when Request model is updated
    return render_template('equipment_maintenance.html', 
                         equipment=equipment_item, 
                         requests=maintenance_requests)

# API Routes for AJAX requests
@app.route('/api/teams')
def api_teams():
    teams = Team.query.all()
    return jsonify([{
        'id': team.id,
        'name': team.name,
        'department': team.department,
        'member_count': len(team.members)
    } for team in teams])

@app.route('/api/members')
def api_members():
    members = TeamMember.query.all()
    return jsonify([{
        'id': member.id,
        'name': member.name,
        'email': member.email,
        'position': member.position,
        'team': member.team.name if member.team else None,
        'status': member.status
    } for member in members])

# Calendar API Routes
@app.route('/api/technicians')
def api_technicians():
    """Get list of technicians for calendar assignment"""
    technicians = TeamMember.query.filter_by(status='active').all()
    return jsonify({
        'technicians': [{
            'id': tech.id,
            'name': tech.name,
            'email': tech.email,
            'position': tech.position
        } for tech in technicians]
    })

@app.route('/api/equipment')
def api_equipment():
    """Get list of equipment for calendar assignment"""
    try:
        equipment = Equipment.query.all()
        return jsonify({
            'equipment': [{
                'id': eq.id,
                'name': eq.name,
                'category': eq.category,
                'location': eq.location,
                'status': eq.status,
                'maintenance_team_id': eq.maintenance_team_id,
                'technician_id': eq.technician_id,
                'employee_id': eq.employee_id
            } for eq in equipment]
        })
    except Exception as e:
        print(f"Error fetching equipment: {e}")
        return jsonify({'equipment': []})

@app.route('/api/requests')
def api_get_requests():
    """Get all maintenance requests for calendar display"""
    try:
        requests = Request.query.all()
        return jsonify({
            'requests': [req.to_dict() for req in requests]
        })
    except:
        return jsonify({'requests': []})

@app.route('/api/requests', methods=['POST'])
def api_create_request():
    """Create a new maintenance request from calendar"""
    data = request.get_json(silent=True) or {}
    
    try:
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        technician_id = data.get('technician_id')
        equipment_id = data.get('equipment_id')
        request_type = data.get('type', 'PREVENTIVE')
        priority = data.get('priority', 'MEDIUM')
        status = data.get('status', 'NEW_REQUEST')
        scheduled_date_str = data.get('scheduled_date')
        due_date_str = data.get('due_date')
        
        # Validation
        if not title:
            return jsonify({'success': False, 'message': 'Title is required'}), 400
        
        if not technician_id:
            return jsonify({'success': False, 'message': 'Technician is required'}), 400
        
        # Parse dates
        from datetime import datetime as dt
        scheduled_date = dt.strptime(scheduled_date_str, '%Y-%m-%d').date() if scheduled_date_str else None
        due_date = dt.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None
        
        # Auto-assign team from equipment if equipment is provided
        team_id = None
        if equipment_id:
            eq = Equipment.query.get(equipment_id)
            if eq and eq.maintenance_team_id:
                team_id = eq.maintenance_team_id
        
        # Create request
        new_request = Request(
            title=title,
            description=description,
            technician_id=int(technician_id),
            equipment_id=int(equipment_id) if equipment_id else None,
            team_id=team_id,
            type=request_type,
            priority=priority,
            status=status,
            scheduled_date=scheduled_date,
            due_date=due_date,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Request created successfully',
            'request': new_request.to_dict()
        })
    except Exception as e:
        print(f"Error creating request: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

