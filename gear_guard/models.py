from extensions import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Placeholder for models
# user.py
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
    
    def __repr__(self):
        return f'<User {self.username}>'

# equipment.py
class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='available')
    category = db.Column(db.String(50))
    location = db.Column(db.String(100))
    assigned_to = db.Column(db.Integer, db.ForeignKey('team_member.id'))
    
    # New fields from wireframe
    company = db.Column(db.String(100))
    used_by = db.Column(db.Integer, db.ForeignKey('team_member.id'))
    maintenance_team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    technician_id = db.Column(db.Integer, db.ForeignKey('team_member.id'))
    employee_id = db.Column(db.Integer, db.ForeignKey('team_member.id'))
    assigned_date = db.Column(db.Date)
    scrap_date = db.Column(db.Date)
    used_in_location = db.Column(db.String(100))
    work_center = db.Column(db.String(100))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    maintenance_team = db.relationship('Team', foreign_keys=[maintenance_team_id], backref='maintained_equipment')
    assignee_member = db.relationship('TeamMember', foreign_keys=[assigned_to], backref='equipment_assigned')
    user_member = db.relationship('TeamMember', foreign_keys=[used_by], backref='equipment_used')
    technician_member = db.relationship('TeamMember', foreign_keys=[technician_id], backref='equipment_maintained')
    responsible_member = db.relationship('TeamMember', foreign_keys=[employee_id], backref='equipment_responsible')
    
    def __repr__(self):
        return f'<Equipment {self.name}>'

# request.py
class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'))
    technician_id = db.Column(db.Integer, db.ForeignKey('team_member.id'))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    status = db.Column(db.String(20), default='NEW_REQUEST')  # NEW_REQUEST, IN_PROGRESS, COMPLETED, CANCELLED
    type = db.Column(db.String(20))  # CORRECTIVE, PREVENTIVE
    priority = db.Column(db.String(20), default='MEDIUM')  # LOW, MEDIUM, HIGH, URGENT
    due_date = db.Column(db.Date)
    scheduled_date = db.Column(db.Date)
    completed_date = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    equipment = db.relationship('Equipment', backref='maintenance_requests')
    technician = db.relationship('TeamMember', foreign_keys=[technician_id], backref='assigned_requests')
    assigned_team = db.relationship('Team', foreign_keys=[team_id], backref='team_requests')
    
    def __repr__(self):
        return f'<Request {self.title}>'
    
    def is_overdue(self):
        """Check if request is overdue"""
        from datetime import date
        if self.due_date and self.status not in ['COMPLETED', 'CANCELLED']:
            return self.due_date < date.today()
        return False
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description or '',
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment.name if self.equipment else None,
            'status': self.status,
            'type': self.type or 'PREVENTIVE',
            'priority': self.priority,
            'dueDate': self.due_date.isoformat() if self.due_date else None,
            'scheduledDate': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'technicianId': self.technician_id,
            'technicianName': self.technician.name if self.technician else None,
            'teamId': self.team_id,
            'teamName': self.assigned_team.name if self.assigned_team else None,
            'isOverdue': self.is_overdue(),
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }

# maintenance_history.py
class MaintenanceHistory(db.Model):
    __tablename__ = 'maintenance_history'
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'))
    action_type = db.Column(db.String(50))  # REPAIR, INSPECTION, REPLACEMENT, CALIBRATION
    description = db.Column(db.Text)
    performed_by = db.Column(db.Integer, db.ForeignKey('team_member.id'))
    performed_date = db.Column(db.DateTime, default=datetime.utcnow)
    cost = db.Column(db.Float)
    downtime_hours = db.Column(db.Float)
    parts_replaced = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    equipment = db.relationship('Equipment', backref='maintenance_history')
    request = db.relationship('Request', backref='history_records')
    technician = db.relationship('TeamMember', backref='maintenance_actions')
    
    def __repr__(self):
        return f'<MaintenanceHistory {self.action_type} for Equipment {self.equipment_id}>'

# team.py
class Team(db.Model):
    __tablename__ = 'team'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    department = db.Column(db.String(100))
    company = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relationship with team members
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Team {self.name}>'

# team_member.py
class TeamMember(db.Model):
    __tablename__ = 'team_member'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))
    position = db.Column(db.String(100))
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'), nullable=False)
    employee_id = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='active')  # active, inactive, on-leave
    joining_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<TeamMember {self.name}>'
