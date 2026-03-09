from app import app
from database.models import User

with app.app_context():
    admins = User.query.filter_by(is_admin=True).all()
    all_users = User.query.all()
    with open('admin_check_output.txt','w') as f:
        f.write(f"Total users: {len(all_users)}\n")
        f.write(f"Admin users: {len(admins)}\n")
        for u in admins:
            f.write(f"ID={u.id}, Email={u.email}, is_admin={u.is_admin}\n")
        if not admins:
            f.write("NO ADMIN USERS FOUND!\n")
