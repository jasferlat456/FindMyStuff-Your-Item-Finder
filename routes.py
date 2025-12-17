from flask import render_template, redirect, url_for, request, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Message
from sqlalchemy import or_
from datetime import datetime, date
import secrets
import string
import re

from models import db, User, Item, Notification
from forms import validate_password

# --- HELPER FUNCTIONS ---

def _convert_drive_link(url):
    """
    Converts a standard Google Drive sharing link into a direct image link.
    This allows the browser to render the image directly in an <img> tag.
    """
    if not url or "drive.google.com" not in url:
        return url
    
    # Regex to extract the File ID from various Drive URL formats
    drive_match = re.search(r'(?:id=|/d/|/file/d/)([a-zA-Z0-9_-]{25,})', url)
    
    if drive_match:
        file_id = drive_match.group(1)
        # Uses the high-reliability direct content endpoint
        return f'https://lh3.googleusercontent.com/u/0/d/{file_id}'
    
    return url

def _format_item_data(item, username):
    """Formats Item data for templates, ensuring dates are string-compatible."""
    return {
        'id': item.id,
        'name': item.name,
        'description': item.description,
        'user_id': item.user_id,
        'owner_username': username,
        'category': item.category,
        'status': item.status,
        'date_lost': item.date_lost.strftime('%Y-%m-%d') if item.date_lost else 'N/A',  
        'picture_url': item.picture_url,
        'is_approved': item.is_approved,
        'contact_email': item.contact_email,    
        'contact_phone': item.contact_phone,
        'item_location': item.item_location,
        'uploader_location': item.uploader_location
    }

# --- ROUTE REGISTRATION ---

def register_routes(app, mail, s):
    
    @app.route('/')
    def home():
        if 'user' in session:
            return redirect(url_for('dashboard'))
        return redirect(url_for('signin'))

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if 'user' in session:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if User.query.filter_by(email=email).first():
                flash("Email already registered!", 'warning')
                return redirect(url_for('signup'))
            
            password_errors = validate_password(password)
            if password_errors:
                flash("Password requirements: " + ", ".join(password_errors), 'error')
                return redirect(url_for('signup'))
                
            if User.query.filter_by(username=username).first():
                flash("Username already exists!", 'warning')
                return redirect(url_for('signup'))

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            new_user = User(username=username, email=email, password=hashed_password, role='user')
            db.session.add(new_user)

            admin = User.query.filter_by(role='admin').first()
            if admin:
                db.session.add(Notification(
                    user_id=admin.id,
                    message=f"New user registered: {username} ({email})",
                    timestamp=datetime.utcnow()
                ))

            db.session.commit()
            flash("Account created successfully! Please sign in.", 'success')
            return redirect(url_for('signin'))
        
        return render_template('signup.html')

    @app.route('/signin', methods=['GET', 'POST'])
    def signin():
        if 'user' in session:
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = User.query.filter_by(username=username).first()
            
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                session['user'] = user.username
                session['role'] = user.role
                flash(f"Welcome back, {user.username}!", 'success')
                return redirect(url_for('dashboard'))
            else:
                flash("Invalid username or password.", 'error')
                
        return render_template('signin.html')

    @app.route('/reset_password_request', methods=['GET', 'POST'])
    def reset_password_request():
        if request.method == 'POST':
            email_input = request.form.get('email')
            user = User.query.filter_by(email=email_input).first()
            if user:
                alphabet = string.ascii_letters + string.digits
                temp_password = ''.join(secrets.choice(alphabet) for i in range(12))
                user.password = generate_password_hash(temp_password)
                db.session.commit()
                
                msg = Message('Your New Temporary Password', recipients=[user.email])
                msg.body = f"Hello {user.username},\n\nYour username: {user.username}\nTemp Password: {temp_password}"
                try:
                    mail.send(msg)
                    flash('A temporary password has been sent to your email.', 'success')
                    return redirect(url_for('signin'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error sending email: {e}', 'error')
            else:
                flash('Email not found.', 'error')
        return render_template('reset_request.html')

    @app.route('/change_password', methods=['GET', 'POST'])
    def change_password():
        if 'user_id' not in session:
            return redirect(url_for('signin'))

        if request.method == 'POST':
            curr = request.form.get('current_password')
            new = request.form.get('new_password')
            conf = request.form.get('confirm_password')
            user = User.query.get(session['user_id'])

            if not check_password_hash(user.password, curr):
                flash("Current password is incorrect!", 'error')
            elif new != conf:
                flash("New passwords do not match!", 'error')
            else:
                errors = validate_password(new)
                if errors:
                    for e in errors: flash(e, 'error')
                else:
                    user.password = generate_password_hash(new)
                    db.session.commit()
                    flash("Password updated successfully!", 'success')
                    return redirect(url_for('dashboard'))
        return render_template('change_password.html')

    @app.route('/dashboard')
    def dashboard():
        if 'user_id' not in session: return redirect(url_for('signin'))
        
        current_role = session.get('role', 'user')
        status = request.args.get('status')
        category = request.args.get('category')
        search = request.args.get('search')
        u_filter = request.args.get('user_filter')
        sort_by = request.args.get('sort_by', 'date_desc')
        
        query = db.session.query(Item, User.username).join(User)

        if current_role == 'user':
            query = query.filter(Item.is_approved == True)
            if u_filter == 'mine': query = query.filter(Item.user_id == session['user_id'])
        elif current_role == 'admin' and u_filter == 'mine':
            query = query.filter(Item.user_id == session['user_id'])

        if status: query = query.filter(Item.status == status)
        if category: query = query.filter(Item.category == category)
        if search:
            pat = f'%{search}%'
            query = query.filter(or_(Item.name.ilike(pat), Item.description.ilike(pat), Item.item_location.ilike(pat)))

        if sort_by == 'name_asc': query = query.order_by(Item.name.asc())
        elif sort_by == 'name_desc': query = query.order_by(Item.name.desc())
        elif sort_by == 'date_asc': query = query.order_by(Item.id.asc())
        else: query = query.order_by(Item.id.desc())
        
        items_data = [_format_item_data(i, u) for i, u in query.all()]
        has_pending = Item.query.filter_by(is_approved=False).count() > 0
        
        context = {
            'username': session['user'], 'current_user_id': session['user_id'],
            'current_role': current_role, 'items': items_data, 'current_sort': sort_by,
            'current_status': status, 'current_category': category, 'current_search': search,
            'current_user_filter': u_filter, 'has_pending_items': has_pending 
        }

        if current_role == 'admin' and u_filter != 'mine':
            return render_template('admin_dashboard.html', **context)
        return render_template('dashboard.html', **context)

    @app.route('/add_item', methods=['GET', 'POST'])
    def add_item():
        if 'user_id' not in session: return redirect(url_for('signin'))
        if session.get('role') == 'admin':
            flash("Admins cannot post new items.", 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            date_str = request.form.get('date_lost')
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else None
            except ValueError:
                flash("Invalid date format.", 'error')
                return redirect(url_for('add_item'))

            # CONVERSION LOGIC FOR GDRIVE
            raw_url = request.form.get('picture_url')
            converted_url = _convert_drive_link(raw_url)

            new_item = Item(
                name=request.form.get('name'), description=request.form.get('description'),
                category=request.form.get('category'), date_lost=date_obj,
                picture_url=converted_url, status=request.form.get('status'),
                contact_email=request.form.get('contact_email'), contact_phone=request.form.get('contact_phone'),
                user_id=session['user_id'], item_location=request.form.get('item_location'),
                uploader_location=request.form.get('uploader_location'), is_approved=False
            )
            db.session.add(new_item)
            
            admin = User.query.filter_by(role='admin').first()
            if admin:
                db.session.add(Notification(user_id=admin.id, message=f"New item '{new_item.name}' needs approval."))
            
            db.session.commit()
            flash(f"Item '{new_item.name}' added! Awaiting admin approval.", 'info')
            return redirect(url_for('dashboard'))
        
        return render_template('add_item.html', max_date=date.today().isoformat())

    @app.route('/moderate_item/<int:item_id>/<action>', methods=['POST'])
    def moderate_item(item_id, action):
        if session.get('role') != 'admin': return redirect(url_for('dashboard'))
        item = Item.query.get_or_404(item_id)

        if action == 'accept':
            item.is_approved = True
            db.session.add(Notification(user_id=item.user_id, message=f"Your item '{item.name}' was approved!"))
            flash(f"Item '{item.name}' approved.", 'success')
        elif action == 'reject':
            reason = request.form.get('rejection_reason')
            if not reason:
                flash("Rejection reason required.", "warning")
                return redirect(url_for('pending_approval'))
            db.session.add(Notification(user_id=item.user_id, message=f"Item '{item.name}' rejected. Reason: {reason}"))
            db.session.delete(item)
            flash(f"Item '{item.name}' rejected.", 'error')
        
        db.session.commit()
        return redirect(url_for('pending_approval'))

    @app.route('/view_item/<int:item_id>')
    def view_item(item_id):
        if 'user_id' not in session: return redirect(url_for('signin'))
        item_data = db.session.query(Item, User.username).join(User).filter(Item.id == item_id).first_or_404()
        item, username = item_data
        
        if not item.is_approved and item.user_id != session['user_id'] and session.get('role') != 'admin':
            flash("This item is pending approval.", 'warning')
            return redirect(url_for('dashboard'))

        return render_template('view_item.html', item=_format_item_data(item, username), 
                               current_user_id=session['user_id'], session_role=session.get('role'))

    @app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
    def edit_item(item_id):
        item = Item.query.get_or_404(item_id)
        if not (item.user_id == session['user_id'] or session.get('role') == 'admin'):
            flash("Unauthorized.", 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            item.name = request.form.get('name')
            item.description = request.form.get('description')
            item.category = request.form.get('category')
            item.status = request.form.get('status')
            item.item_location = request.form.get('item_location')
            item.uploader_location = request.form.get('uploader_location')
            
            raw_url = request.form.get('picture_url')
            if raw_url:
                item.picture_url = _convert_drive_link(raw_url)
                
            db.session.commit()
            flash("Item updated successfully!", "success")
            return redirect(url_for('view_item', item_id=item.id))
            
        return render_template('edit_item.html', item=item, max_date=date.today().isoformat())

    @app.route('/delete_item/<int:item_id>', methods=['POST'])
    def delete_item(item_id):
        if 'user_id' not in session: return redirect(url_for('signin'))
        item = Item.query.get_or_404(item_id)
        
        if item.user_id == session['user_id'] or session.get('role') == 'admin':
            db.session.delete(item)
            db.session.commit()
            flash("Item deleted.", "success")
        else:
            flash("Unauthorized action.", "error")
        return redirect(url_for('dashboard'))

    @app.route('/resolve_item/<int:item_id>', methods=['POST'])
    def resolve_item(item_id):
        item = Item.query.get_or_404(item_id)
        if item.user_id == session['user_id']:
            item.status = 'Claimed'
            admin = User.query.filter_by(role='admin').first()
            if admin:
                db.session.add(Notification(user_id=admin.id, message=f"Item '{item.name}' was claimed."))
            db.session.commit()
            flash("Item marked as Claimed.", 'success')
        return redirect(url_for('view_item', item_id=item.id))

    @app.route('/admin/pending_approval')
    def pending_approval():
        if session.get('role') != 'admin': return redirect(url_for('dashboard'))
        sort_by = request.args.get('sort_by', 'date_asc')
        query = db.session.query(Item, User.username).join(User).filter(Item.is_approved == False)
        
        if sort_by == 'name_asc': query = query.order_by(Item.name.asc())
        elif sort_by == 'name_desc': query = query.order_by(Item.name.desc())
        elif sort_by == 'date_desc': query = query.order_by(Item.id.desc())
        else: query = query.order_by(Item.id.asc())

        items_data = [_format_item_data(i, u) for i, u in query.all()]
        return render_template('pending_approval.html', username=session['user'], items=items_data, current_sort=sort_by)

    @app.route('/my_pending')
    def my_pending():
        if 'user_id' not in session: return redirect(url_for('signin'))
        query = db.session.query(Item, User.username).join(User).filter(Item.user_id == session['user_id'], Item.is_approved == False)
        items_data = [_format_item_data(i, u) for i, u in query.all()]
        return render_template('my_pending.html', username=session['user'], items=items_data)

    @app.route('/admin/delete_all_pending', methods=['POST'])
    def delete_all_pending():
        if session.get('role') != 'admin': return redirect(url_for('dashboard'))
        count = Item.query.filter(Item.is_approved == False).delete()
        db.session.commit()
        flash(f"Deleted {count} pending items.", 'success')
        return redirect(url_for('pending_approval'))

    @app.route('/notifications')
    def notifications():
        if 'user_id' not in session: return redirect(url_for('signin'))
        notifs = Notification.query.filter_by(user_id=session['user_id']).order_by(Notification.timestamp.desc()).all()
        return render_template('notifications.html', notifications=notifs)

    @app.route('/mark_read/<int:notif_id>')
    def mark_read(notif_id):
        n = Notification.query.get_or_404(notif_id)
        if n.user_id == session['user_id']:
            n.is_read = True
            db.session.commit()
        return redirect(url_for('notifications'))

    @app.route('/mark_all_read', methods=['POST'])
    def mark_all_read():
        Notification.query.filter_by(user_id=session['user_id'], is_read=False).update({Notification.is_read: True})
        db.session.commit()
        return redirect(url_for('notifications'))

    @app.route('/logout')
    def logout():
        session.clear()
        flash("Logged out successfully.", 'info')
        return redirect(url_for('signin'))