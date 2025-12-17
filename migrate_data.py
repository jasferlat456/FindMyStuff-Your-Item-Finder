from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app import app, db, User, Item, Notification # Replace your_main_file with your actual filename

# 1. Setup temporary app contexts
sqlite_uri = 'sqlite:///users.db'
mysql_uri = 'mysql+pymysql://root:@localhost/lost_and_found_db'

def migrate():
    with app.app_context():
        # Ensure MySQL tables are created
        app.config['SQLALCHEMY_DATABASE_URI'] = mysql_uri
        db.create_all()
        
        # 2. Extract from SQLite
        print("Reading data from SQLite...")
        app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_uri
        old_users = User.query.all()
        old_items = Item.query.all()
        old_notifs = Notification.query.all()

        # 3. Load into MySQL
        print("Transferring to XAMPP...")
        app.config['SQLALCHEMY_DATABASE_URI'] = mysql_uri
        
        # Clear existing data in MySQL to avoid duplicates
        db.session.query(Notification).delete()
        db.session.query(Item).delete()
        db.session.query(User).delete()

        # Add Users
        for u in old_users:
            new_u = User(id=u.id, username=u.username, email=u.email, password=u.password, role=u.role)
            db.session.add(new_u)
        
        # Add Items
        for i in old_items:
            new_i = Item(
                id=i.id, name=i.name, description=i.description, category=i.category,
                date_lost=i.date_lost, picture_url=i.picture_url, user_id=i.user_id,
                status=i.status, contact_email=i.contact_email, contact_phone=i.contact_phone,
                is_approved=i.is_approved, item_location=i.item_location, uploader_location=i.uploader_location
            )
            db.session.add(new_i)

        # Add Notifications
        for n in old_notifs:
            new_n = Notification(id=n.id, user_id=n.user_id, message=n.message, is_read=n.is_read, timestamp=n.timestamp)
            db.session.add(new_n)

        db.session.commit()
        print("✅ Migration Successful!")

if __name__ == '__main__':
    migrate()