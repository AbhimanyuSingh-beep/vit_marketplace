# ============================================================
# VIT Marketplace - Main Flask Application
# This file is the BRAIN of the entire app.
# It handles all routes (pages), database, login, and chat.
# ============================================================

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import cloudinary
import cloudinary.uploader

# ── App Setup ──────────────────────────────────────────────
app = Flask(__name__)

# Configuration - Get these 3 values from your Cloudinary Dashboard
cloudinary.config( 
  cloud_name = "dxxnlnq0q", 
  api_key = "826648375298161", 
  api_secret = "RPzrigGiFaG4A7xcbgPIgjDqjNI" 
)
app.config['SECRET_KEY'] = 'vit-marketplace-secret-2024'         # Used to secure sessions
# Use the "Pooled connection" string you copied from Neon
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://neondb_owner:npg_VF4HmZXTMl0L@ep-square-breeze-am67vcv6-pooler.c-5.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # SQLite database file

app.config['UPLOAD_FOLDER'] = 'static/uploads'                    # Where item images go
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024               # Max 16MB image upload

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

db = SQLAlchemy(app)           # Database
socketio = SocketIO(app)       # Real-time chat
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ── Database Models ────────────────────────────────────────
# Think of these as Excel sheet columns — they define what data we store

class User(UserMixin, db.Model):
    """Stores every registered user"""
    id       = db.Column(db.Integer, primary_key=True)
    name     = db.Column(db.String(100), nullable=False)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    avatar   = db.Column(db.String(10), default='🎓')   # Emoji avatar
    joined   = db.Column(db.DateTime, default=datetime.utcnow)
    items    = db.relationship('Item', backref='seller', lazy=True)

class Item(db.Model):
    """Stores every item listed for sale"""
    id          = db.Column(db.Integer, primary_key=True)
    title       = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price       = db.Column(db.Float, nullable=False)
    category    = db.Column(db.String(50), nullable=False)
    image       = db.Column(db.String(200), default='no-image.png')
    sold        = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Message(db.Model):
    """Stores all chat messages between users"""
    id         = db.Column(db.Integer, primary_key=True)
    room       = db.Column(db.String(100), nullable=False)  # Unique chat room ID
    sender_id  = db.Column(db.Integer, db.ForeignKey('user.id'))
    content    = db.Column(db.Text, nullable=False)
    timestamp  = db.Column(db.DateTime, default=datetime.utcnow)
    sender     = db.relationship('User', foreign_keys=[sender_id])

# ── Helper Functions ───────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_room_id(user1_id, user2_id):
    """Creates a unique room ID for two users — always the same regardless of order"""
    return f"chat_{min(user1_id, user2_id)}_{max(user1_id, user2_id)}"

# ── Routes (Pages) ─────────────────────────────────────────

@app.route('/')
def home():
    """Home page — shows all available items with search/filter"""
    search   = request.args.get('search', '')
    category = request.args.get('category', '')
    query    = Item.query.filter_by(sold=False)
    if search:
        query = query.filter(Item.title.ilike(f'%{search}%'))
    if category:
        query = query.filter_by(category=category)
    items = query.order_by(Item.created_at.desc()).all()
    categories = ['Books', 'Electronics', 'Furniture', 'Clothing', 'Cycles', 'Other']
    return render_template('home.html', items=items, categories=categories,
                           search=search, selected_category=category)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page — creates a new user account"""
    if request.method == 'POST':
        name     = request.form['name']
        email    = request.form['email']
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'error')
            return redirect(url_for('register'))
        hashed = generate_password_hash(password)  # Never store plain passwords!
        user = User(name=name, email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash('Welcome to VIT Marketplace! 🎉', 'success')
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        user     = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.name}! 👋', 'success')
            return redirect(url_for('home'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/sell', methods=['GET', 'POST'])

@login_required 
def sell():
    """Post a new item for sale"""
    if request.method == 'POST':
        title       = request.form['title']
        description = request.form['description']
        price       = float(request.form['price'])
        category    = request.form['category']
        
        # Default placeholder if no image is uploaded
        image_filename = 'https://via.placeholder.com/300?text=No+Image'

        # --- UPDATED CLOUDINARY UPLOAD SECTION ---
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                # 1. This sends the file to Cloudinary permanently
                upload_result = cloudinary.uploader.upload(file)
                # 2. This gets the full website link (URL) for the photo
                image_filename = upload_result['secure_url'] 
        # ------------------------------------------

        item = Item(title=title, description=description, price=price,
                    category=category, image=image_filename, user_id=current_user.id)
        
        db.session.add(item)
        db.session.commit()
        flash('Item listed successfully! 🚀', 'success')
        return redirect(url_for('home'))
    
    categories = ['Books', 'Electronics', 'Furniture', 'Clothing', 'Cycles', 'Other']
    return render_template('sell.html', categories=categories)
@app.route('/item/<int:item_id>')
def item_detail(item_id):
    """Shows full details of a single item"""
    item = Item.query.get_or_404(item_id)
    return render_template('item_detail.html', item=item)

@app.route('/mark_sold/<int:item_id>')
@login_required
def mark_sold(item_id):
    """Seller marks their item as sold"""
    item = Item.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        item.sold = True
        db.session.commit()
        flash('Item marked as sold!', 'success')
    return redirect(url_for('profile'))

@app.route('/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    if item.user_id == current_user.id:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted!', 'success')
    return redirect(url_for('profile'))
@app.route('/inbox')

@login_required
def inbox():
    user_id = current_user.id
    # Look for any chat room involving the current user
    all_messages = Message.query.filter(
        (Message.room.like(f"chat_{user_id}_%")) | 
        (Message.room.like(f"chat_%_{user_id}"))
    ).order_by(Message.timestamp.desc()).all()

    unique_chats = {}
    for msg in all_messages:
        if msg.room not in unique_chats:
            parts = msg.room.split('_')
            # Figure out who the OTHER person in the room is
            other_id = int(parts[1]) if int(parts[2]) == user_id else int(parts[2])
            other_user = User.query.get(other_id)
            
            unique_chats[msg.room] = {
                'user': other_user,
                'last_msg': msg.content,
                'time': msg.timestamp.strftime('%I:%M %p')
            }

    return render_template('inbox.html', chats=unique_chats.values())


@app.route('/profile')
@login_required
def profile():
    """Shows logged-in user's own listings"""
    items = Item.query.filter_by(user_id=current_user.id).order_by(Item.created_at.desc()).all()
    return render_template('profile.html', items=items)

@app.route('/chat/<int:other_user_id>')
@login_required
def chat(other_user_id):
    """Chat page between current user and another user"""
    other_user = User.query.get_or_404(other_user_id)
    room       = get_room_id(current_user.id, other_user_id)
    messages   = Message.query.filter_by(room=room).order_by(Message.timestamp).all()
    return render_template('chat.html', other_user=other_user, room=room, messages=messages)

# ── Socket.IO Events (Real-time Chat) ─────────────────────
@socketio.on('join')
def on_join(data):
    """User joins a chat room"""
    join_room(data['room'])

@socketio.on('message')
def handle_message(data):
    """Receives a message and broadcasts it to the room"""
    msg = Message(room=data['room'], sender_id=current_user.id, content=data['message'])
    db.session.add(msg)
    db.session.commit()
    emit('message', {
        'sender': current_user.name,
        'message': data['message'],
        'time': datetime.utcnow().strftime('%I:%M %p')
    }, room=data['room'])

# ── Start the App ──────────────────────────────────────────
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Creates all database tables if they don't exist
        # Create uploads folder if missing
        os.makedirs('static/uploads', exist_ok=True)
    print("🚀 VIT Marketplace running at http://127.0.0.1:5000")
    socketio.run(app, debug=True)
