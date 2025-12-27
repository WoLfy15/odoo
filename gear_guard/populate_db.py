"""
Script to populate the GearGuard database with sample data for testing
"""
from app import app, db, Team, TeamMember, Equipment, Request
from datetime import datetime, timedelta, date

def populate_database():
    with app.app_context():
        # Clear existing data (optional - comment out if you want to keep existing data)
        print("Clearing existing data...")
        Request.query.delete()
        Equipment.query.delete()
        TeamMember.query.delete()
        Team.query.delete()
        
        # Create Teams
        print("Creating teams...")
        teams = [
            Team(name="Electrical Team", description="Handles all electrical equipment maintenance", department="Maintenance", company="Adani"),
            Team(name="Mechanical Team", description="Handles mechanical equipment", department="Maintenance", company="Adani"),
            Team(name="HVAC Team", description="Heating, ventilation, and air conditioning", department="Facilities", company="Adani")
        ]
        db.session.add_all(teams)
        db.session.commit()
        
        # Create Team Members
        print("Creating team members...")
        members = [
            # Electrical Team
            TeamMember(employee_id="EMP0001", name="Rajesh Kumar", email="rajesh.kumar@adani.com", position="Senior Technician", 
                      phone="9876543210", team_id=teams[0].id, status="active", joining_date=date(2020, 1, 15)),
            TeamMember(employee_id="EMP0002", name="Priya Sharma", email="priya.sharma@adani.com", position="Technician", 
                      phone="9876543211", team_id=teams[0].id, status="active", joining_date=date(2021, 3, 10)),
            
            # Mechanical Team
            TeamMember(employee_id="EMP0003", name="Amit Patel", email="amit.patel@adani.com", position="Lead Mechanic", 
                      phone="9876543212", team_id=teams[1].id, status="active", joining_date=date(2019, 5, 20)),
            TeamMember(employee_id="EMP0004", name="Sunita Verma", email="sunita.verma@adani.com", position="Mechanic", 
                      phone="9876543213", team_id=teams[1].id, status="active", joining_date=date(2022, 2, 1)),
            
            # HVAC Team
            TeamMember(employee_id="EMP0005", name="Mohammed Ali", email="mohammed.ali@adani.com", position="HVAC Specialist", 
                      phone="9876543214", team_id=teams[2].id, status="active", joining_date=date(2020, 8, 15)),
        ]
        db.session.add_all(members)
        db.session.commit()
        
        # Create Equipment
        print("Creating equipment...")
        equipment_list = [
            Equipment(
                name="CNC Machine #1",
                category="Manufacturing",
                location="Factory Floor A",
                status="IN_USE",
                company="Adani",
                used_in_location="Factory Floor A",
                work_center="Production Line 1",
                description="Primary CNC machine for precision parts. Fanuc Robodrill α-D21MiB5",
                maintenance_team_id=teams[1].id,  # Mechanical Team
                technician_id=members[2].id,  # Amit Patel (Lead Mechanic)
            ),
            Equipment(
                name="Transformer Unit #3",
                category="Electrical",
                location="Electrical Room B",
                status="AVAILABLE",
                company="Adani",
                description="Backup transformer, 500 kVA capacity. ABB DTR-500kVA",
                maintenance_team_id=teams[0].id,  # Electrical Team
                technician_id=members[0].id,  # Rajesh Kumar (Senior Technician)
            ),
            Equipment(
                name="HVAC Unit - Building C",
                category="HVAC",
                location="Building C Roof",
                status="UNDER_MAINTENANCE",
                company="Adani",
                description="Central air conditioning for Building C. Carrier AquaEdge 19DV",
                maintenance_team_id=teams[2].id,  # HVAC Team
                technician_id=members[4].id,  # Mohammed Ali (HVAC Specialist)
            ),
            Equipment(
                name="Hydraulic Press",
                category="Manufacturing",
                location="Factory Floor B",
                status="AVAILABLE",
                company="Adani",
                work_center="Pressing Station",
                description="250-ton hydraulic press for metal forming. Schuler HP-250",
                maintenance_team_id=teams[1].id,  # Mechanical Team
                technician_id=members[3].id,  # Sunita Verma (Mechanic)
            ),
            Equipment(
                name="Backup Generator",
                category="Electrical",
                location="Generator Room",
                status="AVAILABLE",
                company="Adani",
                description="550 kW diesel generator for emergency power. Cummins C550D6",
                maintenance_team_id=teams[0].id,  # Electrical Team
                technician_id=members[1].id,  # Priya Sharma (Technician)
            ),
        ]
        db.session.add_all(equipment_list)
        db.session.commit()
        
        # Create Sample Requests
        print("Creating sample maintenance requests...")
        today = date.today()
        requests = [
            Request(
                title="PREVENTIVE Maintenance - CNC Machine #1",
                description="Scheduled quarterly maintenance including lubrication, calibration, and inspection",
                equipment_id=equipment_list[0].id,
                technician_id=members[2].id,
                team_id=teams[1].id,
                type="PREVENTIVE",
                priority="MEDIUM",
                status="NEW_REQUEST",
                scheduled_date=today + timedelta(days=5),
                due_date=today + timedelta(days=10),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
            Request(
                title="CORRECTIVE Maintenance - Transformer Unit #3",
                description="Unusual humming noise detected. Need immediate inspection.",
                equipment_id=equipment_list[1].id,
                technician_id=members[0].id,
                team_id=teams[0].id,
                type="CORRECTIVE",
                priority="HIGH",
                status="IN_PROGRESS",
                scheduled_date=today,
                due_date=today + timedelta(days=2),
                created_at=datetime.utcnow() - timedelta(days=1),
                updated_at=datetime.utcnow()
            ),
            Request(
                title="CORRECTIVE Maintenance - HVAC Unit - Building C",
                description="Temperature control malfunction. Building C overheating.",
                equipment_id=equipment_list[2].id,
                technician_id=members[4].id,
                team_id=teams[2].id,
                type="CORRECTIVE",
                priority="URGENT",
                status="IN_PROGRESS",
                scheduled_date=today - timedelta(days=2),
                due_date=today,
                created_at=datetime.utcnow() - timedelta(days=3),
                updated_at=datetime.utcnow()
            ),
            Request(
                title="PREVENTIVE Maintenance - Hydraulic Press",
                description="Monthly inspection and oil change",
                equipment_id=equipment_list[3].id,
                technician_id=members[3].id,
                team_id=teams[1].id,
                type="PREVENTIVE",
                priority="LOW",
                status="UNDER_REVIEW",
                scheduled_date=today - timedelta(days=10),
                due_date=today - timedelta(days=5),
                completed_date=today - timedelta(days=5),
                actual_hours=3.5,
                created_at=datetime.utcnow() - timedelta(days=15),
                updated_at=datetime.utcnow() - timedelta(days=5)
            ),
            Request(
                title="CORRECTIVE Maintenance - Backup Generator",
                description="Generator failed to start during weekly test",
                equipment_id=equipment_list[4].id,
                technician_id=members[1].id,
                team_id=teams[0].id,
                type="CORRECTIVE",
                priority="HIGH",
                status="NEW_REQUEST",
                scheduled_date=today + timedelta(days=1),
                due_date=today + timedelta(days=3),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            ),
        ]
        db.session.add_all(requests)
        db.session.commit()
        
        print("\n" + "="*60)
        print("✅ DATABASE POPULATED SUCCESSFULLY!")
        print("="*60)
        print(f"\nCreated:")
        print(f"  - {len(teams)} Teams")
        print(f"  - {len(members)} Team Members")
        print(f"  - {len(equipment_list)} Equipment")
        print(f"  - {len(requests)} Maintenance Requests")
        print("\nSample Data:")
        print("\nTeams:")
        for team in teams:
            print(f"  - {team.name} ({team.department})")
        print("\nTechnicians:")
        for member in members:
            print(f"  - {member.name} ({member.position}) - {member.employee_id}")
        print("\nEquipment:")
        for eq in equipment_list:
            tech = next((m for m in members if m.id == eq.technician_id), None)
            print(f"  - {eq.name} → Assigned to: {tech.name if tech else 'None'}")
        print("\nRequests:")
        for req in requests:
            overdue = " [OVERDUE]" if req.is_overdue() else ""
            print(f"  - {req.title} ({req.type}, {req.priority}, {req.status}){overdue}")
        print("\n" + "="*60)
        print("You can now test the auto-assignment feature!")
        print("Visit: http://127.0.0.1:5000/calendar")
        print("="*60 + "\n")

if __name__ == "__main__":
    populate_database()
