import sys
sys.path.insert(0, 'gear_guard')

from app import app, db

with app.app_context():
    db.create_all()
    print('Database initialized successfully!')
