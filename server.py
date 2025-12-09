from flask import Flask, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=['http://127.0.0.1:5000', 'http://localhost:5000'])
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS

# Database configuration - works with both PostgreSQL (production) and SQLite (local)
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Render uses postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    # Local development with SQLite in instance folder (persists across restarts)
    import os
    instance_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance')
    if not os.path.exists(instance_path):
        os.makedirs(instance_path)
    db_path = os.path.join(instance_path, 'tasks.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Verify connections before using them
    'pool_recycle': 300,    # Recycle connections every 5 minutes
    'pool_size': 10,        # Connection pool size
    'max_overflow': 20      # Allow overflow connections
}

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.String(50), nullable=True)
    tasks = db.relationship('Task', backref='owner', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)  # Soft delete for admin tracking
    deleted_at = db.Column(db.String(50), nullable=True)
    
    # Core prioritization fields
    priority = db.Column(db.String(20), default='medium')
    category = db.Column(db.String(50), default='general')
    due_date = db.Column(db.String(50), nullable=True)
    estimated_time = db.Column(db.Integer, default=30)
    importance = db.Column(db.Integer, default=3)
    created_at = db.Column(db.String(50), nullable=True)
    
    # Advanced fields
    energy_level = db.Column(db.String(20), default='medium')  # low, medium, high
    dependencies = db.Column(db.String(200), nullable=True)  # Comma-separated task IDs
    completed_at = db.Column(db.String(50), nullable=True)
    actual_time_spent = db.Column(db.Integer, nullable=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    text = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.String(50), nullable=True)
    is_approved = db.Column(db.Boolean, default=True)  # Admin can moderate

class UserActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)  # login, add_task, delete_task, etc.
    ip_address = db.Column(db.String(50), nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)  # mobile, desktop, tablet
    browser = db.Column(db.String(100), nullable=True)
    os = db.Column(db.String(100), nullable=True)
    location_country = db.Column(db.String(100), nullable=True)
    location_city = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(500), nullable=True)  # Extra info as JSON string

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Helper function to log user activity
def log_activity(user_id, action, details=None):
    from datetime import datetime
    
    # Get request info
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent', '')
    
    # Parse user agent for device info
    device_type = 'desktop'
    if 'mobile' in user_agent.lower():
        device_type = 'mobile'
    elif 'tablet' in user_agent.lower():
        device_type = 'tablet'
    
    # Parse browser
    browser = 'Unknown'
    if 'Chrome' in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent:
        browser = 'Safari'
    elif 'Edge' in user_agent:
        browser = 'Edge'
    
    # Parse OS
    os_name = 'Unknown'
    if 'Windows' in user_agent:
        os_name = 'Windows'
    elif 'Mac' in user_agent:
        os_name = 'MacOS'
    elif 'Linux' in user_agent:
        os_name = 'Linux'
    elif 'Android' in user_agent:
        os_name = 'Android'
    elif 'iOS' in user_agent or 'iPhone' in user_agent:
        os_name = 'iOS'
    
    activity = UserActivity(
        user_id=user_id,
        action=action,
        ip_address=ip,
        user_agent=user_agent[:500],
        device_type=device_type,
        browser=browser,
        os=os_name,
        timestamp=datetime.now().isoformat(),
        details=details
    )
    
    try:
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error logging activity: {e}")

# Create tables and admin user
with app.app_context():
    try:
        db.create_all()
        print("✅ Database tables created/verified")
    except Exception as e:
        print(f"⚠️ Error creating tables: {e}")
    
    # Create permanent admin account
    admin_email = "kalanadenuz@gmail.com"
    
    try:
        admin = User.query.filter_by(email=admin_email).first()
        
        if not admin:
            from datetime import datetime
            admin = User(
                email=admin_email,
                is_admin=True,
                created_at=datetime.now().isoformat()
            )
            admin.set_password("12345678")
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin account created: {admin_email}")
        else:
            # Ensure admin status is set
            if not admin.is_admin:
                admin.is_admin = True
                db.session.commit()
                print(f"✅ Admin status granted to: {admin_email}")
            else:
                print(f"✅ Admin account exists: {admin_email}")
    except Exception as e:
        db.session.rollback()
        print(f"⚠️ Error with admin account: {e}")
        try:
            # If error, try creating tables and admin again
            db.create_all()
            from datetime import datetime
            admin = User(
                email=admin_email,
                is_admin=True,
                created_at=datetime.now().isoformat()
            )
            admin.set_password("12345678")
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Admin account created on retry: {admin_email}")
        except Exception as retry_error:
            db.session.rollback()
            print(f"❌ Failed to create admin: {retry_error}")

@app.route('/')
def home():
    from flask import send_file
    return send_file('login.html')

@app.route('/login.html')
def login_page():
    from flask import send_file
    return send_file('login.html')

@app.route('/register.html')
def register_page():
    from flask import send_file
    return send_file('register.html')

@app.route('/index.html')
def index_page():
    from flask import send_file
    return send_file('index.html')

@app.route('/styles.css')
def styles():
    from flask import send_file
    return send_file('styles.css', mimetype='text/css')

@app.route('/auth-styles.css')
def auth_styles():
    from flask import send_file
    return send_file('auth-styles.css', mimetype='text/css')

@app.route('/script.js')
def script():
    from flask import send_file
    return send_file('script.js', mimetype='application/javascript')

@app.route('/learn.html')
def learn_page():
    from flask import send_file
    return send_file('learn.html')

# Authentication Routes
@app.route('/register', methods=['POST'])
def register():
    from datetime import datetime
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"success": False, "message": "Email and password required"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email already registered"}), 400
    
    user = User(email=email, created_at=datetime.now().isoformat())
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # Log registration
    log_activity(user.id, 'register', f'New user registered: {email}')
    
    return jsonify({"success": True, "message": "Registration successful! Please login."})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        login_user(user)
        log_activity(user.id, 'login', f'User logged in: {email}')
        return jsonify({"success": True, "message": "Login successful", "email": user.email})
    
    return jsonify({"success": False, "message": "Invalid email or password"}), 401

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    log_activity(current_user.id, 'logout', f'User logged out: {current_user.email}')
    logout_user()
    return jsonify({"success": True, "message": "Logged out successfully"})

@app.route('/check-auth')
def check_auth():
    if current_user.is_authenticated:
        return jsonify({"authenticated": True, "email": current_user.email, "is_admin": current_user.is_admin})
    return jsonify({"authenticated": False})

@app.route('/add-task', methods=['POST'])
@login_required
def add_task():
    data = request.get_json()
    text = data.get('text', '')
    priority = data.get('priority', 'medium')
    category = data.get('category', 'general')
    due_date = data.get('due_date')
    estimated_time = data.get('estimated_time', 30)
    importance = data.get('importance', 3)
    
    if not text:
        return jsonify({"success": False, "message": "Task text required"}), 400
    
    from datetime import datetime
    task = Task(
        text=text,
        user_id=current_user.id,
        priority=priority,
        category=category,
        due_date=due_date,
        estimated_time=estimated_time,
        importance=importance,
        created_at=datetime.now().isoformat()
    )
    db.session.add(task)
    db.session.commit()
    
    # Log activity
    log_activity(current_user.id, 'add_task', f'Added task: {text[:50]}')
    
    return jsonify({"success": True, "task": {
        "id": task.id,
        "text": task.text,
        "completed": task.completed,
        "priority": task.priority,
        "category": task.category,
        "due_date": task.due_date,
        "estimated_time": task.estimated_time,
        "importance": task.importance
    }})

@app.route('/tasks')
@login_required
def get_tasks():
    tasks = Task.query.filter_by(user_id=current_user.id, is_deleted=False).all()
    task_list = [{
        "id": t.id,
        "text": t.text,
        "completed": t.completed,
        "priority": t.priority,
        "category": t.category,
        "due_date": t.due_date,
        "estimated_time": t.estimated_time,
        "importance": t.importance,
        "created_at": t.created_at
    } for t in tasks]
    return jsonify({"tasks": task_list})

@app.route('/task/<int:task_id>/complete', methods=['PUT'])
@login_required
def toggle_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first()
    if not task:
        return jsonify({"success": False, "message": "Task not found"}), 404
    
    task.completed = not task.completed
    db.session.commit()
    
    # Log activity
    action = 'complete_task' if task.completed else 'uncomplete_task'
    log_activity(current_user.id, action, f'{action.replace("_", " ").title()}: {task.text[:50]}')
    
    return jsonify({"success": True, "completed": task.completed})

@app.route('/task/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    from datetime import datetime
    task = Task.query.filter_by(id=task_id, user_id=current_user.id, is_deleted=False).first()
    if not task:
        return jsonify({"success": False, "message": "Task not found"}), 404
    
    # Save task name before soft delete
    task_name = task.text
    
    # Soft delete for admin tracking
    task.is_deleted = True
    task.deleted_at = datetime.now().isoformat()
    db.session.commit()
    
    # Log activity
    log_activity(current_user.id, 'delete_task', f'Deleted task: {task_name[:50]}')
    
    return jsonify({"success": True, "message": "Task deleted"})

@app.route('/suggest', methods=['POST'])
@login_required
def suggest():
    from priority_algorithm import calculate_master_priority, create_daily_plan
    
    # Get all pending tasks for the user
    tasks = Task.query.filter_by(user_id=current_user.id, completed=False).all()
    
    if not tasks:
        return jsonify({
            "suggestion": "No pending tasks! Add some tasks to get started.",
            "ordered_tasks": [],
            "daily_plan": None
        })

    # Create daily plan using advanced algorithm
    daily_plan, top_tasks = create_daily_plan(tasks, max_tasks=10)
    
    # Calculate priority scores for all tasks
    scored_tasks = []
    for task in tasks:
        score, reasons, time_rec = calculate_master_priority(task)
        scored_tasks.append({
            'task': task,
            'score': score,
            'reasons': reasons,
            'time_recommendation': time_rec
        })
    
    # Sort by score (highest first)
    scored_tasks.sort(key=lambda x: x['score'], reverse=True)
    
    # Build ordered task list
    ordered_tasks = []
    for i, item in enumerate(scored_tasks[:15], 1):  # Top 15 tasks
        task = item['task']
        ordered_tasks.append({
            'rank': i,
            'text': task.text,
            'priority': task.priority,
            'category': task.category,
            'due_date': task.due_date,
            'estimated_time': task.estimated_time,
            'importance': task.importance,
            'score': item['score'],
            'reasons': item['reasons'],
            'time_recommendation': item['time_recommendation']
        })
    
    # Generate smart suggestion
    top_task = scored_tasks[0]['task']
    top_reasons = scored_tasks[0]['reasons']
    top_time_rec = scored_tasks[0]['time_recommendation']
    
    suggestion_text = f"🎯 Start with: '{top_task.text}'"
    if top_reasons:
        suggestion_text += f" — {', '.join(top_reasons[:2])}"
    
    if top_task.estimated_time:
        suggestion_text += f" ({top_task.estimated_time} min)"
    
    # Build daily plan summary
    plan_summary = {
        'total_time_minutes': daily_plan['total_time'],
        'total_time_hours': round(daily_plan['total_time'] / 60, 1),
        'morning_focus': [{
            'text': item['task'].text,
            'time': item['task'].estimated_time,
            'reasons': item['reasons'][:2]
        } for item in daily_plan['morning_focus']],
        'quick_wins': [{
            'text': item['task'].text,
            'time': item['task'].estimated_time
        } for item in daily_plan['quick_wins']],
        'afternoon_tasks': [{
            'text': item['task'].text,
            'time': item['task'].estimated_time
        } for item in daily_plan['afternoon']]
    }
    
    return jsonify({
        "suggestion": suggestion_text,
        "ordered_tasks": ordered_tasks,
        "total_pending": len(tasks),
        "total_time_needed": sum(t.estimated_time for t in tasks),
        "daily_plan": plan_summary,
        "top_time_recommendation": top_time_rec
    })

# Review System Routes
@app.route('/reviews', methods=['GET'])
def get_reviews():
    reviews = Review.query.filter_by(is_approved=True).order_by(Review.created_at.desc()).limit(20).all()
    review_list = [{
        'id': r.id,
        'rating': r.rating,
        'text': r.text,
        'user_email': r.author.email.split('@')[0] + '***',  # Anonymize
        'created_at': r.created_at
    } for r in reviews]
    return jsonify({'reviews': review_list})

@app.route('/add-review', methods=['POST'])
@login_required
def add_review():
    from datetime import datetime
    data = request.get_json()
    rating = data.get('rating')
    text = data.get('text', '').strip()
    
    if not rating or rating < 1 or rating > 5:
        return jsonify({"success": False, "message": "Rating must be 1-5 stars"}), 400
    
    # Check if user already reviewed
    existing = Review.query.filter_by(user_id=current_user.id).first()
    if existing:
        return jsonify({"success": False, "message": "You've already submitted a review"}), 400
    
    review = Review(
        user_id=current_user.id,
        rating=int(rating),
        text=text[:500],  # Max 500 chars
        created_at=datetime.now().isoformat()
    )
    db.session.add(review)
    db.session.commit()
    
    # Log activity
    log_activity(current_user.id, 'add_review', f'Submitted {rating}-star review')
    
    return jsonify({"success": True, "message": "Thank you for your review!"})

# Admin Routes
@app.route('/admin.html')
@login_required
def admin_page():
    if not current_user.is_admin:
        return "Access Denied", 403
    from flask import send_file
    return send_file('admin.html')

@app.route('/admin/stats', methods=['GET'])
@login_required
def admin_stats():
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    from sqlalchemy import func
    
    total_users = User.query.count()
    total_tasks = Task.query.count()
    active_tasks = Task.query.filter_by(is_deleted=False, completed=False).count()
    completed_tasks = Task.query.filter_by(completed=True).count()
    deleted_tasks = Task.query.filter_by(is_deleted=True).count()
    total_reviews = Review.query.count()
    avg_rating = db.session.query(func.avg(Review.rating)).scalar() or 0
    
    return jsonify({
        'total_users': total_users,
        'total_tasks': total_tasks,
        'active_tasks': active_tasks,
        'completed_tasks': completed_tasks,
        'deleted_tasks': deleted_tasks,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 2)
    })

@app.route('/admin/users', methods=['GET'])
@login_required
def admin_users():
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    users = User.query.all()
    user_list = [{
        'id': u.id,
        'email': u.email,
        'is_admin': u.is_admin,
        'created_at': u.created_at,
        'task_count': len(u.tasks),
        'completed_count': len([t for t in u.tasks if t.completed]),
        'deleted_count': len([t for t in u.tasks if t.is_deleted])
    } for u in users]
    
    return jsonify({'users': user_list})

@app.route('/admin/user/<int:user_id>/tasks', methods=['GET'])
@login_required
def admin_user_tasks(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Get all tasks including deleted
    tasks = Task.query.filter_by(user_id=user_id).all()
    task_list = [{
        'id': t.id,
        'text': t.text,
        'completed': t.completed,
        'is_deleted': t.is_deleted,
        'priority': t.priority,
        'category': t.category,
        'created_at': t.created_at,
        'completed_at': t.completed_at,
        'deleted_at': t.deleted_at
    } for t in tasks]
    
    return jsonify({
        'user_email': user.email,
        'tasks': task_list
    })

@app.route('/admin/all-tasks', methods=['GET'])
@login_required
def admin_all_tasks():
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    # Get all tasks from all users with user information
    tasks = Task.query.all()
    task_list = [{
        'id': t.id,
        'text': t.text,
        'user_email': t.owner.email,
        'user_id': t.user_id,
        'completed': t.completed,
        'is_deleted': t.is_deleted,
        'priority': t.priority,
        'category': t.category,
        'created_at': t.created_at,
        'completed_at': t.completed_at,
        'deleted_at': t.deleted_at,
        'estimated_time': t.estimated_time,
        'importance': t.importance
    } for t in tasks]
    
    return jsonify({
        'total_tasks': len(task_list),
        'tasks': task_list
    })

@app.route('/admin/activities', methods=['GET'])
@login_required
def admin_activities():
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    # Get recent activities
    limit = request.args.get('limit', 100, type=int)
    activities = UserActivity.query.order_by(UserActivity.timestamp.desc()).limit(limit).all()
    
    activity_list = [{
        'id': a.id,
        'user_id': a.user_id,
        'user_email': db.session.get(User, a.user_id).email if db.session.get(User, a.user_id) else 'Unknown',
        'action': a.action,
        'ip_address': a.ip_address,
        'device_type': a.device_type,
        'browser': a.browser,
        'os': a.os,
        'location_country': a.location_country,
        'location_city': a.location_city,
        'timestamp': a.timestamp,
        'details': a.details
    } for a in activities]
    
    return jsonify({
        'total': len(activity_list),
        'activities': activity_list
    })

@app.route('/admin/user/<int:user_id>/activities', methods=['GET'])
@login_required
def admin_user_activities(user_id):
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    activities = UserActivity.query.filter_by(user_id=user_id).order_by(UserActivity.timestamp.desc()).all()
    
    activity_list = [{
        'id': a.id,
        'action': a.action,
        'ip_address': a.ip_address,
        'device_type': a.device_type,
        'browser': a.browser,
        'os': a.os,
        'timestamp': a.timestamp,
        'details': a.details
    } for a in activities]
    
    return jsonify({
        'user_email': user.email,
        'total_activities': len(activity_list),
        'activities': activity_list
    })

@app.route('/admin/analytics', methods=['GET'])
@login_required
def admin_analytics():
    if not current_user.is_admin:
        return jsonify({"error": "Access denied"}), 403
    
    from sqlalchemy import func
    
    # Device analytics
    device_stats = db.session.query(
        UserActivity.device_type,
        func.count(UserActivity.id)
    ).group_by(UserActivity.device_type).all()
    
    # Browser analytics
    browser_stats = db.session.query(
        UserActivity.browser,
        func.count(UserActivity.id)
    ).group_by(UserActivity.browser).all()
    
    # OS analytics
    os_stats = db.session.query(
        UserActivity.os,
        func.count(UserActivity.id)
    ).group_by(UserActivity.os).all()
    
    # Action analytics
    action_stats = db.session.query(
        UserActivity.action,
        func.count(UserActivity.id)
    ).group_by(UserActivity.action).all()
    
    # Most active users
    active_users = db.session.query(
        UserActivity.user_id,
        func.count(UserActivity.id).label('activity_count')
    ).group_by(UserActivity.user_id).order_by(func.count(UserActivity.id).desc()).limit(10).all()
    
    active_users_list = [{
        'user_id': u[0],
        'user_email': db.session.get(User, u[0]).email if db.session.get(User, u[0]) else 'Unknown',
        'activity_count': u[1]
    } for u in active_users]
    
    return jsonify({
        'devices': {d[0] or 'unknown': d[1] for d in device_stats},
        'browsers': {b[0] or 'unknown': b[1] for b in browser_stats},
        'operating_systems': {o[0] or 'unknown': o[1] for o in os_stats},
        'actions': {a[0]: a[1] for a in action_stats},
        'most_active_users': active_users_list
    })

# Error handlers for database consistency
@app.errorhandler(Exception)
def handle_exception(e):
    # Rollback any pending database transactions on error
    db.session.rollback()
    print(f"Error: {e}")
    return jsonify({"error": "An error occurred", "message": str(e)}), 500

@app.teardown_appcontext
def shutdown_session(exception=None):
    # Ensure database sessions are cleaned up properly
    db.session.remove()

# Health check endpoint
@app.route('/health')
def health_check():
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "database": "disconnected", "error": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
