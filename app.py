from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
from difflib import SequenceMatcher

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://ragejax:p3f10tIgHrWtFOUYKVSpz6Kpf9fcviWS@dpg-d5ndd175r7bs73dmp0f0-a.singapore-postgres.render.com/lostandfound_g9aj'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def calculate_similarity(text1, text2):
    """Calculate similarity score between two texts (0-1)"""
    text1 = text1.lower().strip()
    text2 = text2.lower().strip()
    return SequenceMatcher(None, text1, text2).ratio()

def find_matching_items(title, description, item_type='lost'):
    """Find matching items from the opposite category"""
    similarity_threshold = 0.5
    
    if item_type == 'lost':
        # If user posted a lost item, find matching found items
        potential_matches = FoundItem.query.filter_by(status='found').all()
    else:
        # If user posted a found item, find matching lost items
        potential_matches = LostItem.query.filter_by(status='lost').all()
    
    matches = []
    for item in potential_matches:
        # Calculate similarity between titles and descriptions
        title_similarity = calculate_similarity(title, item.title)
        desc_similarity = calculate_similarity(description, item.description)
        
        # Average similarity score
        avg_similarity = (title_similarity + desc_similarity) / 2
        
        if avg_similarity >= similarity_threshold:
            matches.append({
                'item': item,
                'similarity_score': avg_similarity,
                'item_type': 'found' if item_type == 'lost' else 'lost'
            })
    
    # Sort by similarity score (highest first)
    matches.sort(key=lambda x: x['similarity_score'], reverse=True)
    return matches

def create_match_notification(item_id, item_type, matches):
    """Create a notification message for matched items"""
    if not matches:
        return None
    
    # Get the top match
    top_match = matches[0]
    match_score = int(top_match['similarity_score'] * 100)
    matched_item = top_match['item']
    
    if item_type == 'lost':
        title = f"🎉 Found Match: {matched_item.title}"
        message = f"Great news! We found a {match_score}% match for your lost item.\n\n"
        message += f"Found Item: {matched_item.title}\n"
        message += f"Location: {matched_item.location}\n"
        message += f"Found by: {matched_item.user.username}\n\n"
        message += f"Check it out and contact them if it's yours!"
        notification_type = "match_found"
    else:
        title = f"🎉 Lost Item Match: {matched_item.title}"
        message = f"Great news! We found a {match_score}% match for the item you found.\n\n"
        message += f"Lost Item: {matched_item.title}\n"
        message += f"Lost Location: {matched_item.location}\n"
        message += f"Lost by: {matched_item.user.username}\n\n"
        message += f"They might be looking for this item!"
        notification_type = "lost_match_found"
    
    return {
        'title': title,
        'message': message,
        'type': notification_type,
        'match_count': len(matches),
        'top_match_id': matched_item.id,
        'top_match_type': top_match['item_type']
    }


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    lost_items = db.relationship('LostItem', backref='user', lazy=True)
    found_items = db.relationship('FoundItem', backref='user', lazy=True)

class LostItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    date_lost = db.Column(db.Date, nullable=False)
    contact_info = db.Column(db.String(200), nullable=False)
    picture = db.Column(db.String(255), nullable=True)
    adviser_name = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='lost')  # lost, found, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class FoundItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    date_found = db.Column(db.Date, nullable=False)
    contact_info = db.Column(db.String(200), nullable=False)
    picture = db.Column(db.String(255), nullable=True)
    adviser_name = db.Column(db.String(200), nullable=True)
    status = db.Column(db.String(20), default='found')  # found, claimed, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    item_type = db.Column(db.String(10), nullable=False)  # 'lost' or 'found'
    item_id = db.Column(db.Integer, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Location fields
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    address = db.Column(db.String(500), nullable=True)
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    lost_items = LostItem.query.filter_by(status='lost').order_by(LostItem.created_at.desc()).limit(6).all()
    found_items = FoundItem.query.filter_by(status='found').order_by(FoundItem.created_at.desc()).limit(6).all()
    return render_template('index.html', lost_items=lost_items, found_items=found_items)

@app.route('/reports')
def reports():
    """Display statistics and reports"""
    # Count statistics
    total_users = User.query.count()
    total_lost_items = LostItem.query.count()
    total_found_items = FoundItem.query.count()
    active_lost = LostItem.query.filter_by(status='lost').count()
    active_found = FoundItem.query.filter_by(status='found').count()
    closed_lost = LostItem.query.filter_by(status='closed').count()
    closed_found = FoundItem.query.filter_by(status='closed').count()
    
    # Items matching status
    items_found = LostItem.query.filter_by(status='found').count()
    items_claimed = FoundItem.query.filter_by(status='claimed').count()
    
    # Total messages
    total_messages = Message.query.count()
    
    # Recently reported items
    recent_items = []
    recent_lost = LostItem.query.order_by(LostItem.created_at.desc()).limit(3).all()
    recent_found = FoundItem.query.order_by(FoundItem.created_at.desc()).limit(3).all()
    
    stats = {
        'total_users': total_users,
        'total_lost_items': total_lost_items,
        'total_found_items': total_found_items,
        'active_lost': active_lost,
        'active_found': active_found,
        'closed_lost': closed_lost,
        'closed_found': closed_found,
        'items_found': items_found,
        'items_claimed': items_claimed,
        'total_messages': total_messages,
        'recent_lost': recent_lost,
        'recent_found': recent_found
    }
    
    return render_template('reports.html', stats=stats)

@app.route('/webpushr-sw.js')
def webpushr_service_worker():
    """Serve the WebPushR service worker from root to maintain scope"""
    return send_file('static/webpushr-sw.js', mimetype='application/javascript')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        agree_terms = request.form.get('agree_terms')
        
        # Validation
        if not username or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if not agree_terms:
            flash('You must agree to the Terms and Conditions and Privacy Policy.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/lost-items')
def lost_items():
    search = request.args.get('search', '')
    if search:
        items = LostItem.query.filter_by(status='lost').filter(
            (LostItem.title.ilike(f'%{search}%')) |
            (LostItem.description.ilike(f'%{search}%')) |
            (LostItem.location.ilike(f'%{search}%'))
        ).order_by(LostItem.created_at.desc()).all()
    else:
        items = LostItem.query.filter_by(status='lost').order_by(LostItem.created_at.desc()).all()
    return render_template('lost_items.html', items=items, search=search)

@app.route('/found-items')
def found_items():
    search = request.args.get('search', '')
    if search:
        items = FoundItem.query.filter_by(status='found').filter(
            (FoundItem.title.ilike(f'%{search}%')) |
            (FoundItem.description.ilike(f'%{search}%')) |
            (FoundItem.location.ilike(f'%{search}%'))
        ).order_by(FoundItem.created_at.desc()).all()
    else:
        items = FoundItem.query.filter_by(status='found').order_by(FoundItem.created_at.desc()).all()
    return render_template('found_items.html', items=items, search=search)

@app.route('/search')
def search():
    search_query = request.args.get('q', '').strip()
    item_type = request.args.get('type', 'both')  # both, lost, found
    
    if not search_query:
        return redirect(url_for('index'))
    
    lost_results = []
    found_results = []
    
    if item_type in ['both', 'lost']:
        lost_results = LostItem.query.filter_by(status='lost').filter(
            (LostItem.title.ilike(f'%{search_query}%')) |
            (LostItem.description.ilike(f'%{search_query}%')) |
            (LostItem.location.ilike(f'%{search_query}%'))
        ).order_by(LostItem.created_at.desc()).all()
    
    if item_type in ['both', 'found']:
        found_results = FoundItem.query.filter_by(status='found').filter(
            (FoundItem.title.ilike(f'%{search_query}%')) |
            (FoundItem.description.ilike(f'%{search_query}%')) |
            (FoundItem.location.ilike(f'%{search_query}%'))
        ).order_by(FoundItem.created_at.desc()).all()
    
    return render_template('search.html', search_query=search_query, lost_items=lost_results, found_items=found_results, item_type=item_type)

@app.route('/report-lost', methods=['GET', 'POST'])
@login_required
def report_lost():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        date_lost = request.form.get('date_lost')
        contact_info = request.form.get('contact_info')
        adviser_name = request.form.get('adviser_name')
        
        if not all([title, description, location, date_lost, contact_info]):
            flash('All required fields are required.', 'error')
            return render_template('report_lost.html')
        
        # Handle file upload
        picture_path = None
        if 'picture' in request.files:
            file = request.files['picture']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to make filename unique
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                picture_path = filename
        
        item = LostItem(
            title=title,
            description=description,
            location=location,
            date_lost=datetime.strptime(date_lost, '%Y-%m-%d').date(),
            contact_info=contact_info,
            picture=picture_path,
            adviser_name=adviser_name,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        
        # Find matching items
        matches = find_matching_items(title, description, 'lost')
        if matches:
            flash(f'Lost item reported! We found {len(matches)} matching found item(s) that might be yours!', 'info')
        else:
            flash('Lost item reported successfully!', 'success')
        
        return redirect(url_for('lost_item_detail', item_id=item.id))
    
    return render_template('report_lost.html')

@app.route('/report-found', methods=['GET', 'POST'])
@login_required
def report_found():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        location = request.form.get('location')
        date_found = request.form.get('date_found')
        contact_info = request.form.get('contact_info')
        adviser_name = request.form.get('adviser_name')
        
        if not all([title, description, location, date_found, contact_info]):
            flash('All required fields are required.', 'error')
            return render_template('report_found.html')
        
        # Handle file upload
        picture_path = None
        if 'picture' in request.files:
            file = request.files['picture']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to make filename unique
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                picture_path = filename
        
        item = FoundItem(
            title=title,
            description=description,
            location=location,
            date_found=datetime.strptime(date_found, '%Y-%m-%d').date(),
            contact_info=contact_info,
            picture=picture_path,
            adviser_name=adviser_name,
            user_id=current_user.id
        )
        db.session.add(item)
        db.session.commit()
        
        # Find matching items
        matches = find_matching_items(title, description, 'found')
        if matches:
            flash(f'Found item reported! We found {len(matches)} matching lost item(s) that might belong to someone!', 'info')
        else:
            flash('Found item reported successfully!', 'success')
        
        return redirect(url_for('found_item_detail', item_id=item.id))
    
    return render_template('report_found.html')

@app.route('/lost-item/<int:item_id>')
def lost_item_detail(item_id):
    item = LostItem.query.get_or_404(item_id)
    matches = find_matching_items(item.title, item.description, 'lost')
    return render_template('item_detail.html', item=item, item_type='lost', matches=matches)

@app.route('/found-item/<int:item_id>')
def found_item_detail(item_id):
    item = FoundItem.query.get_or_404(item_id)
    matches = find_matching_items(item.title, item.description, 'found')
    return render_template('item_detail.html', item=item, item_type='found', matches=matches)

@app.route('/my-items')
@login_required
def my_items():
    lost = LostItem.query.filter_by(user_id=current_user.id).order_by(LostItem.created_at.desc()).all()
    found = FoundItem.query.filter_by(user_id=current_user.id).order_by(FoundItem.created_at.desc()).all()
    return render_template('my_items.html', lost_items=lost, found_items=found)

@app.route('/update-status/<item_type>/<int:item_id>/<status>')
@login_required
def update_status(item_type, item_id, status):
    if item_type == 'lost':
        item = LostItem.query.get_or_404(item_id)
        if item.user_id != current_user.id:
            flash('You do not have permission to update this item.', 'error')
            return redirect(url_for('my_items'))
    else:
        item = FoundItem.query.get_or_404(item_id)
        if item.user_id != current_user.id:
            flash('You do not have permission to update this item.', 'error')
            return redirect(url_for('my_items'))
    
    item.status = status
    db.session.commit()
    flash('Status updated successfully!', 'success')
    return redirect(url_for('my_items'))

@app.route('/send-message/<item_type>/<int:item_id>', methods=['POST'])
@login_required
def send_message(item_type, item_id):
    if item_type == 'lost':
        item = LostItem.query.get_or_404(item_id)
    else:
        item = FoundItem.query.get_or_404(item_id)
    
    # Can't send message to yourself
    if item.user_id == current_user.id:
        flash('You cannot send a message to yourself.', 'error')
        return redirect(url_for('lost_item_detail' if item_type == 'lost' else 'found_item_detail', item_id=item_id))
    
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('lost_item_detail' if item_type == 'lost' else 'found_item_detail', item_id=item_id))
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=item.user_id,
        content=content,
        item_type=item_type,
        item_id=item_id
    )
    db.session.add(message)
    db.session.commit()
    
    flash('Message sent successfully!', 'success')
    return redirect(url_for('lost_item_detail' if item_type == 'lost' else 'found_item_detail', item_id=item_id))

@app.route('/messages')
@login_required
def messages():
    # Get all conversations (received messages)
    received = Message.query.filter_by(recipient_id=current_user.id).order_by(Message.created_at.desc()).all()
    
    # Get unique senders for conversation list
    conversations = {}
    for msg in received:
        sender_id = msg.sender_id
        if sender_id not in conversations:
            conversations[sender_id] = {
                'sender': msg.sender,
                'last_message': msg,
                'unread_count': 0
            }
        if not msg.is_read:
            conversations[sender_id]['unread_count'] += 1
    
    # Get matching items for current user's lost items
    lost_matches = []
    user_lost_items = LostItem.query.filter_by(user_id=current_user.id, status='lost').all()
    for lost_item in user_lost_items:
        matches = find_matching_items(lost_item.title, lost_item.description, 'lost')
        if matches:
            lost_matches.append({
                'your_item': lost_item,
                'matches': matches[:3],  # Top 3 matches
                'item_type': 'lost'
            })
    
    # Get matching items for current user's found items
    found_matches = []
    user_found_items = FoundItem.query.filter_by(user_id=current_user.id, status='found').all()
    for found_item in user_found_items:
        matches = find_matching_items(found_item.title, found_item.description, 'found')
        if matches:
            found_matches.append({
                'your_item': found_item,
                'matches': matches[:3],  # Top 3 matches
                'item_type': 'found'
            })
    
    all_matches = lost_matches + found_matches
    
    return render_template('messages.html', conversations=conversations, all_matches=all_matches)

@app.route('/conversation/<int:user_id>')
@login_required
def conversation(user_id):
    other_user = User.query.get_or_404(user_id)
    
    # Get all messages between current user and other user
    messages_list = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()
    
    # Mark received messages as read
    unread = Message.query.filter_by(sender_id=user_id, recipient_id=current_user.id, is_read=False).all()
    for msg in unread:
        msg.is_read = True
    db.session.commit()
    
    return render_template('conversation.html', other_user=other_user, messages=messages_list)

@app.route('/send-reply/<int:user_id>', methods=['POST'])
@login_required
def send_reply(user_id):
    other_user = User.query.get_or_404(user_id)
    content = request.form.get('content', '').strip()
    
    if not content:
        flash('Message cannot be empty.', 'error')
    else:
        message = Message(
            sender_id=current_user.id,
            recipient_id=user_id,
            content=content,
            item_type='reply',
            item_id=0
        )
        db.session.add(message)
        db.session.commit()
        flash('Message sent successfully!', 'success')
    
    return redirect(url_for('conversation', user_id=user_id))

@app.route('/send-location/<int:user_id>', methods=['POST'])
@login_required
def send_location(user_id):
    """Send a location message"""
    import json
    
    other_user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    address = data.get('address', 'Location')
    
    if not latitude or not longitude:
        return {'error': 'Location data missing'}, 400
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=user_id,
        content=f"📍 Location shared: {address}",
        item_type='location',
        item_id=0,
        latitude=latitude,
        longitude=longitude,
        address=address
    )
    db.session.add(message)
    db.session.commit()
    
    return {'success': True, 'message_id': message.id}

@app.route('/unread-count')
@login_required
def unread_count():
    # Count unread messages
    unread_messages = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    
    # Count matched items
    matched_items_count = 0
    
    # Get matching items for current user's lost items
    user_lost_items = LostItem.query.filter_by(user_id=current_user.id, status='lost').all()
    for lost_item in user_lost_items:
        matches = find_matching_items(lost_item.title, lost_item.description, 'lost')
        if matches:
            matched_items_count += len(matches)
    
    # Get matching items for current user's found items
    user_found_items = FoundItem.query.filter_by(user_id=current_user.id, status='found').all()
    for found_item in user_found_items:
        matches = find_matching_items(found_item.title, found_item.description, 'found')
        if matches:
            matched_items_count += len(matches)
    
    # Total unread/new notifications
    total_notifications = unread_messages + matched_items_count
    
    return {
        'unread_count': unread_messages,
        'matched_items': matched_items_count,
        'total_notifications': total_notifications
    }

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

