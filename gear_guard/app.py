from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_migrate import Migrate
from config import Config
from extensions import db
from models import *
from datetime import datetime
import re

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

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
    
    return render_template('dashboard.html', 
                         total_teams=total_teams,
                         total_members=total_members,
                         total_equipment=total_equipment,
                         active_members=active_members)

@app.route('/equipment')
def equipment():
    return render_template('equipment.html')

@app.route('/request')
def request_form():
    return render_template('request_form.html')

@app.route('/kanban')
def kanban():
    return render_template('kanban.html')

@app.route('/calendar')
def calendar():
    return render_template('calendar.html')

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
        
        new_team = Team(name=name, description=description, department=department)
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
        employee_id = request.form.get('employee_id')
        joining_date_str = request.form.get('joining_date')
        action = request.form.get('action', 'done')
        
        joining_date = datetime.strptime(joining_date_str, '%Y-%m-%d').date() if joining_date_str else None

        # Validations
        errors = []
        if not name:
            errors.append('Name is required.')
        if not email:
            errors.append('Email is required.')
        if not team_id:
            errors.append('Team selection is required.')
        if phone and not re.fullmatch(r"\d{10}", phone):
            errors.append('Phone number must be exactly 10 digits.')

        # Friendly duplicate checks
        if employee_id and TeamMember.query.filter_by(employee_id=employee_id).first():
            errors.append('Employee ID already exists. Please use a unique code.')
        if TeamMember.query.filter_by(email=email).first():
            errors.append('Email already exists. Please use a unique email.')
        if phone and TeamMember.query.filter_by(phone=phone).first():
            errors.append('Phone number already exists. Please use a unique phone number.')
        if TeamMember.query.filter_by(name=name).first():
            errors.append('A member with the same name already exists.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            teams = Team.query.all()
            form_data = {
                'name': name,
                'email': email,
                'phone': phone,
                'position': position,
                'team_id': team_id,
                'employee_id': employee_id,
                'joining_date': joining_date_str or ''
            }
            return render_template('add_member.html', teams=teams, form_data=form_data)

        # Auto-assign employee code if missing
        if not employee_id:
            count = TeamMember.query.count() + 1
            employee_id = f"EMP{count:04d}"

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
    suggested_employee_id = generate_employee_id()
    return render_template('add_member.html', teams=teams, suggested_employee_id=suggested_employee_id)

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

        # Validations and duplicate checks (excluding current member)
        errors = []
        if member.phone and not re.fullmatch(r"\d{10}", member.phone):
            errors.append('Phone number must be exactly 10 digits.')
        if member.employee_id:
            existing_emp = TeamMember.query.filter(TeamMember.employee_id == member.employee_id, TeamMember.id != member.id).first()
            if existing_emp:
                errors.append('Employee ID already exists. Please use a unique code.')
        existing_email = TeamMember.query.filter(TeamMember.email == member.email, TeamMember.id != member.id).first()
        if existing_email:
            errors.append('Email already exists. Please use a unique email.')
        if member.phone:
            existing_phone = TeamMember.query.filter(TeamMember.phone == member.phone, TeamMember.id != member.id).first()
            if existing_phone:
                errors.append('Phone number already exists. Please use a unique phone number.')
        existing_name = TeamMember.query.filter(TeamMember.name == member.name, TeamMember.id != member.id).first()
        if existing_name:
            errors.append('A member with the same name already exists.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            teams = Team.query.all()
            return render_template('edit_member.html', member=member, teams=teams)

        # Auto-assign employee code if missing
        if not member.employee_id:
            count = TeamMember.query.count() + 1
            member.employee_id = f"EMP{count:04d}"

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

if __name__ == "__main__":
    app.run(debug=True)
