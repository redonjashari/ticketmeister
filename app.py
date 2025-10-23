from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename
import os
from dotenv import load_dotenv
from db_connection import get_db_connection as get_conn
from functools import wraps
import secrets
from datetime import datetime, timedelta

load_dotenv()  # reads .env

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'img')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, user_id, username, person_id, is_admin):
        self.id = user_id
        self.username = username
        self.person_id = person_id
        self.is_admin = is_admin

@login_manager.user_loader
def load_user(user_id):
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, username, person_id, is_admin 
                FROM users 
                WHERE user_id = %s AND is_active = 1
            """, (user_id,))
            user_data = cur.fetchone()
            if user_data:
                return User(user_data[0], user_data[1], user_data[2], user_data[3])
    except:
        pass
    return None

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# ============== HOME & MAIN PAGES ==============

@app.route("/")
def home():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Get upcoming events with concert details
            cur.execute("""
                SELECT 
                    e.event_id,
                    e.title,
                    e.start_time,
                    e.e_description,
                    v.v_name,
                    v.city,
                    ce.genre,
                    MIN(t.face_value) as min_price,
                    COUNT(DISTINCT CASE WHEN t.ticket_status = 'available' THEN t.ticket_id END) as available_tickets,
                    e.image_path
                FROM events e
                JOIN venues v ON e.venue_id = v.venue_id
                LEFT JOIN concert_events ce ON e.event_id = ce.event_id
                LEFT JOIN tickets t ON e.event_id = t.event_id
                WHERE e.start_time > NOW() AND e.e_status = 'scheduled'
                GROUP BY e.event_id
                ORDER BY e.start_time ASC
                LIMIT 12
            """)
            upcoming_events = cur.fetchall()
            
            # Get featured event (The Weeknd specifically, or fallback to next big event)
            cur.execute("""
                SELECT 
                    e.event_id,
                    e.title,
                    e.start_time,
                    e.e_description,
                    v.v_name,
                    v.city,
                    ce.genre,
                    e.image_path
                FROM events e
                JOIN venues v ON e.venue_id = v.venue_id
                LEFT JOIN concert_events ce ON e.event_id = ce.event_id
                WHERE e.start_time > NOW() AND e.e_status = 'scheduled'
                AND (e.title LIKE '%Weeknd%' OR e.title LIKE '%weeknd%')
                ORDER BY e.start_time ASC
                LIMIT 1
            """)
            featured_event = cur.fetchone()
            
            # If no Weeknd event found, fallback to next upcoming event
            if not featured_event:
                cur.execute("""
                    SELECT 
                        e.event_id,
                        e.title,
                        e.start_time,
                        e.e_description,
                        v.v_name,
                        v.city,
                        ce.genre,
                        e.image_path
                    FROM events e
                    JOIN venues v ON e.venue_id = v.venue_id
                    LEFT JOIN concert_events ce ON e.event_id = ce.event_id
                    WHERE e.start_time > NOW() AND e.e_status = 'scheduled'
                    ORDER BY e.start_time ASC
                    LIMIT 1
                """)
                featured_event = cur.fetchone()
            
    except Exception as e:
        print(f"Error loading home page: {e}")
        upcoming_events = []
        featured_event = None
    
    return render_template("index.html", 
                         upcoming_events=upcoming_events,
                         featured_event=featured_event)

@app.route("/search")
def search():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    e.event_id,
                    e.title,
                    e.start_time,
                    v.v_name,
                    v.city,
                    ce.genre,
                    MIN(t.face_value) as min_price
                FROM events e
                JOIN venues v ON e.venue_id = v.venue_id
                LEFT JOIN concert_events ce ON e.event_id = ce.event_id
                LEFT JOIN tickets t ON e.event_id = t.event_id
                WHERE (e.title LIKE %s OR v.v_name LIKE %s OR ce.genre LIKE %s)
                    AND e.start_time > NOW()
                    AND e.e_status = 'scheduled'
                GROUP BY e.event_id
                ORDER BY e.start_time ASC
                LIMIT 10
            """, (f'%{query}%', f'%{query}%', f'%{query}%'))
            results = cur.fetchall()
            
            search_results = []
            for row in results:
                search_results.append({
                    'event_id': row[0],
                    'title': row[1],
                    'date': row[2].strftime('%b %d, %Y') if row[2] else '',
                    'venue': f"{row[3]}, {row[4]}" if row[3] and row[4] else '',
                    'genre': row[5] or '',
                    'price': f"€{row[6]:.0f}" if row[6] else 'TBA'
                })
            
            return jsonify(search_results)
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify([])

@app.route("/event/<int:event_id>")
def event_details(event_id):
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Get event details
            cur.execute("""
                SELECT 
                    e.event_id,
                    e.title,
                    e.e_description,
                    e.start_time,
                    e.end_time,
                    v.v_name,
                    v.v_address,
                    v.city,
                    v.country,
                    v.capacity,
                    ce.genre,
                    ce.is_outdoor,
                    e.image_path
                FROM events e
                JOIN venues v ON e.venue_id = v.venue_id
                LEFT JOIN concert_events ce ON e.event_id = ce.event_id
                WHERE e.event_id = %s
            """, (event_id,))
            event = cur.fetchone()
            
            if not event:
                flash('Event not found.', 'error')
                return redirect(url_for('home'))
            
            # Get available tickets
            cur.execute("""
                SELECT 
                    t.ticket_id,
                    t.face_value,
                    t.currency,
                    s.seat_section,
                    s.row_label,
                    s.seat_number,
                    CASE WHEN vt.ticket_id IS NOT NULL THEN 'VIP' ELSE 'Regular' END as ticket_type,
                    vt.vip_level,
                    vt.perks
                FROM tickets t
                LEFT JOIN seats s ON t.seat_id = s.seat_id
                LEFT JOIN vip_tickets vt ON t.ticket_id = vt.ticket_id
                WHERE t.event_id = %s 
                    AND t.ticket_status = 'available'
                    AND NOT EXISTS (
                        SELECT 1 FROM purchase_items pi WHERE pi.ticket_id = t.ticket_id
                    )
                ORDER BY t.face_value ASC
            """, (event_id,))
            tickets = cur.fetchall()
            
            # Get performers
            cur.execute("""
                SELECT 
                    p.first_name,
                    p.last_name,
                    a.stage_name,
                    perf.is_headliner
                FROM performances perf
                JOIN artists a ON perf.artist_id = a.person_id
                JOIN persons p ON a.person_id = p.person_id
                WHERE perf.event_id = %s
                ORDER BY perf.is_headliner DESC, perf.set_order ASC
            """, (event_id,))
            performers = cur.fetchall()
            
    except Exception as e:
        print(f"Error loading event details: {e}")
        flash('Error loading event details.', 'error')
        return redirect(url_for('home'))
    
    return render_template("event_details.html", 
                         event=event,
                         tickets=tickets,
                         performers=performers)

@app.route("/genres")
def genres():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Get all unique genres with event counts
            cur.execute("""
                SELECT 
                    ce.genre,
                    COUNT(DISTINCT e.event_id) as event_count,
                    MIN(e.start_time) as next_event_date
                FROM concert_events ce
                JOIN events e ON ce.event_id = e.event_id
                WHERE e.start_time > NOW() AND e.e_status = 'scheduled'
                GROUP BY ce.genre
                ORDER BY event_count DESC, ce.genre ASC
            """)
            genres_list = cur.fetchall()
            
    except Exception as e:
        print(f"Error loading genres: {e}")
        genres_list = []
    
    return render_template("genres.html", genres=genres_list)

@app.route("/genre/<path:genre_name>")
def genre_events(genre_name):
    from urllib.parse import unquote
    # Decode the URL-encoded genre name
    genre_name = unquote(genre_name)
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    e.event_id,
                    e.title,
                    e.start_time,
                    v.v_name,
                    v.city,
                    ce.genre,
                    MIN(t.face_value) as min_price,
                    e.image_path
                FROM events e
                JOIN concert_events ce ON e.event_id = ce.event_id
                JOIN venues v ON e.venue_id = v.venue_id
                LEFT JOIN tickets t ON e.event_id = t.event_id
                WHERE ce.genre = %s
                    AND e.start_time > NOW()
                    AND e.e_status = 'scheduled'
                GROUP BY e.event_id
                ORDER BY e.start_time ASC
            """, (genre_name,))
            events = cur.fetchall()
            
    except Exception as e:
        print(f"Error loading genre events: {e}")
        events = []
    
    return render_template("genre_events.html", 
                         genre=genre_name,
                         events=events)

# ============== AUTHENTICATION ==============

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        if not username or not password:
            flash("Please provide both username and password.", "error")
            return render_template("login.html")
        
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, username, password_hash, person_id, is_admin, is_active
                    FROM users 
                    WHERE username = %s
                """, (username,))
                user_data = cur.fetchone()
                
                if user_data and user_data[5]:  # is_active
                    if bcrypt.check_password_hash(user_data[2], password):
                        user = User(user_data[0], user_data[1], user_data[3], user_data[4])
                        login_user(user)
                        
                        # Update last login
                        cur.execute("""
                            UPDATE users SET last_login = NOW() WHERE user_id = %s
                        """, (user_data[0],))
                        conn.commit()
                        
                        flash(f"Welcome back, {username}!", "success")
                        next_page = request.args.get('next')
                        return redirect(next_page if next_page else url_for('home'))
                
                flash("Invalid username or password.", "error")
        except Exception as e:
            print(f"Login error: {e}")
            flash("An error occurred during login. Please try again.", "error")
    
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip() or None
        
        # Validation
        if not all([username, password, first_name, last_name, email]):
            flash("Please fill in all required fields.", "error")
            return render_template("register.html")
        
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        
        if len(password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("register.html")
        
        try:
            with get_conn() as conn, conn.cursor() as cur:
                # Check if username exists
                cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
                if cur.fetchone():
                    flash("Username already exists. Please choose another.", "error")
                    return render_template("register.html")
                
                # Check if email exists
                cur.execute("SELECT person_id FROM persons WHERE email = %s", (email,))
                if cur.fetchone():
                    flash("Email already registered.", "error")
                    return render_template("register.html")
                
                # Create person record
                cur.execute("""
                    INSERT INTO persons (first_name, last_name, email, phone)
                    VALUES (%s, %s, %s, %s)
                """, (first_name, last_name, email, phone))
                person_id = cur.lastrowid
                
                # Create customer record
                cur.execute("""
                    INSERT INTO customers (person_id, loyalty_points)
                    VALUES (%s, 0)
                """, (person_id,))
                
                # Create user record
                password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
                cur.execute("""
                    INSERT INTO users (person_id, username, password_hash, is_admin)
                    VALUES (%s, %s, %s, 0)
                """, (person_id, username, password_hash))
                
                conn.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))
                
        except Exception as e:
            print(f"Registration error: {e}")
            flash("An error occurred during registration. Please try again.", "error")
    
    return render_template("register.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        
        if not email:
            flash("Please provide your email address.", "error")
            return render_template("forgot_password.html")
        
        try:
            with get_conn() as conn, conn.cursor() as cur:
                # Check if email exists
                cur.execute("""
                    SELECT u.user_id, p.email 
                    FROM users u
                    JOIN persons p ON u.person_id = p.person_id
                    WHERE p.email = %s AND u.is_active = 1
                """, (email,))
                user_data = cur.fetchone()
                
                if user_data:
                    # Generate reset token
                    reset_token = secrets.token_urlsafe(32)
                    expiry = datetime.now() + timedelta(hours=1)
                    
                    cur.execute("""
                        UPDATE users 
                        SET reset_token = %s, reset_token_expiry = %s
                        WHERE user_id = %s
                    """, (reset_token, expiry, user_data[0]))
                    conn.commit()
                    
                    # In a real app, send email here
                    flash(f"Password reset link (for demo): /reset-password/{reset_token}", "info")
                else:
                    # Don't reveal if email exists
                    flash("If an account with that email exists, a reset link has been sent.", "info")
                
                return redirect(url_for('login'))
                
        except Exception as e:
            print(f"Forgot password error: {e}")
            flash("An error occurred. Please try again.", "error")
    
    return render_template("forgot_password.html")

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT user_id, reset_token_expiry 
                FROM users 
                WHERE reset_token = %s
            """, (token,))
            user_data = cur.fetchone()
            
            if not user_data or datetime.now() > user_data[1]:
                flash("Invalid or expired reset token.", "error")
                return redirect(url_for('forgot_password'))
            
            if request.method == "POST":
                password = request.form.get("password", "")
                confirm_password = request.form.get("confirm_password", "")
                
                if password != confirm_password:
                    flash("Passwords do not match.", "error")
                    return render_template("reset_password.html", token=token)
                
                if len(password) < 6:
                    flash("Password must be at least 6 characters long.", "error")
                    return render_template("reset_password.html", token=token)
                
                # Update password
                password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
                cur.execute("""
                    UPDATE users 
                    SET password_hash = %s, reset_token = NULL, reset_token_expiry = NULL
                    WHERE user_id = %s
                """, (password_hash, user_data[0]))
                conn.commit()
                
                flash("Password reset successful! Please log in.", "success")
                return redirect(url_for('login'))
                
    except Exception as e:
        print(f"Reset password error: {e}")
        flash("An error occurred. Please try again.", "error")
        return redirect(url_for('forgot_password'))
    
    return render_template("reset_password.html", token=token)

# ============== PROFILE ==============

@app.route("/profile")
@login_required
def profile():
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Get user personal info
            cur.execute("""
                SELECT p.person_id, p.first_name, p.last_name, p.email, p.phone, 
                       p.date_of_birth, c.loyalty_points, u.username, u.created_at
                FROM users u
                LEFT JOIN persons p ON u.person_id = p.person_id
                LEFT JOIN customers c ON p.person_id = c.person_id
                WHERE u.user_id = %s
            """, (current_user.id,))
            user_info = cur.fetchone()
            
            # Get purchase history
            cur.execute("""
                SELECT 
                    pur.purchase_id,
                    pur.purchase_time,
                    pur.total_amount,
                    pur.purch_status,
                    e.title,
                    e.start_time,
                    v.v_name,
                    COUNT(pi.ticket_id) as ticket_count
                FROM purchases pur
                JOIN purchase_items pi ON pur.purchase_id = pi.purchase_id
                JOIN tickets t ON pi.ticket_id = t.ticket_id
                JOIN events e ON t.event_id = e.event_id
                JOIN venues v ON e.venue_id = v.venue_id
                WHERE pur.customer_id = %s
                GROUP BY pur.purchase_id
                ORDER BY pur.purchase_time DESC
            """, (current_user.person_id,))
            purchases = cur.fetchall()
            
    except Exception as e:
        print(f"Profile error: {e}")
        user_info = None
        purchases = []
    
    return render_template("profile.html", user_info=user_info, purchases=purchases)

@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip() or None
        date_of_birth = request.form.get("date_of_birth") or None
        
        if not all([first_name, last_name, email]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('edit_profile'))
        
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    UPDATE persons 
                    SET first_name = %s, last_name = %s, email = %s, 
                        phone = %s, date_of_birth = %s
                    WHERE person_id = %s
                """, (first_name, last_name, email, phone, date_of_birth, current_user.person_id))
                conn.commit()
                flash("Profile updated successfully!", "success")
                return redirect(url_for('profile'))
                
        except Exception as e:
            print(f"Edit profile error: {e}")
            flash("An error occurred. Please try again.", "error")
    
    # Get current user info
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT first_name, last_name, email, phone, date_of_birth
                FROM persons
                WHERE person_id = %s
            """, (current_user.person_id,))
            user_info = cur.fetchone()
    except:
        user_info = None
    
    return render_template("edit_profile.html", user_info=user_info)

# ============== TICKET PURCHASE FLOW ==============

@app.route("/purchase/select-tickets/<int:event_id>", methods=["POST"])
@login_required
def select_tickets(event_id):
    selected_tickets = request.form.getlist('tickets[]')
    
    if not selected_tickets:
        flash("Please select at least one ticket.", "error")
        return redirect(url_for('event_details', event_id=event_id))
    
    # Store in session for checkout
    session['cart'] = {
        'event_id': event_id,
        'ticket_ids': selected_tickets
    }
    
    return redirect(url_for('checkout'))

@app.route("/checkout")
@login_required
def checkout():
    cart = session.get('cart')
    if not cart:
        flash("Your cart is empty.", "error")
        return redirect(url_for('home'))
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Get event details
            cur.execute("""
                SELECT e.event_id, e.title, e.start_time, v.v_name, v.city
                FROM events e
                JOIN venues v ON e.venue_id = v.venue_id
                WHERE e.event_id = %s
            """, (cart['event_id'],))
            event = cur.fetchone()
            
            # Get ticket details
            placeholders = ','.join(['%s'] * len(cart['ticket_ids']))
            cur.execute(f"""
                SELECT 
                    t.ticket_id,
                    t.face_value,
                    t.currency,
                    s.seat_section,
                    s.row_label,
                    s.seat_number,
                    CASE WHEN vt.ticket_id IS NOT NULL THEN 'VIP' ELSE 'Regular' END as ticket_type
                FROM tickets t
                LEFT JOIN seats s ON t.seat_id = s.seat_id
                LEFT JOIN vip_tickets vt ON t.ticket_id = vt.ticket_id
                WHERE t.ticket_id IN ({placeholders})
                    AND t.ticket_status = 'available'
            """, cart['ticket_ids'])
            tickets = cur.fetchall()
            
            total = sum(ticket[1] for ticket in tickets)
            
    except Exception as e:
        print(f"Checkout error: {e}")
        flash("Error loading checkout. Please try again.", "error")
        return redirect(url_for('home'))
    
    return render_template("checkout.html", 
                         event=event,
                         tickets=tickets,
                         total=total)

@app.route("/purchase/complete", methods=["POST"])
@login_required
def complete_purchase():
    cart = session.get('cart')
    if not cart:
        flash("Your cart is empty.", "error")
        return redirect(url_for('home'))
    
    payment_method = request.form.get('payment_method', 'card')
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Calculate total
            placeholders = ','.join(['%s'] * len(cart['ticket_ids']))
            cur.execute(f"""
                SELECT SUM(face_value)
                FROM tickets
                WHERE ticket_id IN ({placeholders})
            """, cart['ticket_ids'])
            total = cur.fetchone()[0] or 0
            
            # Create purchase
            cur.execute("""
                INSERT INTO purchases (customer_id, total_amount, purch_status)
                VALUES (%s, %s, 'completed')
            """, (current_user.person_id, total))
            purchase_id = cur.lastrowid
            
            # Add purchase items
            for ticket_id in cart['ticket_ids']:
                cur.execute("""
                    SELECT face_value FROM tickets WHERE ticket_id = %s
                """, (ticket_id,))
                price = cur.fetchone()[0]
                
                cur.execute("""
                    INSERT INTO purchase_items (purchase_id, ticket_id, price_paid)
                    VALUES (%s, %s, %s)
                """, (purchase_id, ticket_id, price))
                
                # Update ticket status
                cur.execute("""
                    UPDATE tickets SET ticket_status = 'sold' WHERE ticket_id = %s
                """, (ticket_id,))
            
            # Create payment record
            transaction_ref = f"TX-{purchase_id}-{secrets.token_hex(4).upper()}"
            cur.execute("""
                INSERT INTO payments (purchase_id, amount, method, transaction_ref, payment_status)
                VALUES (%s, %s, %s, %s, 'ok')
            """, (purchase_id, total, payment_method, transaction_ref))
            
            conn.commit()
            
            # Clear cart
            session.pop('cart', None)
            
            flash("Purchase completed successfully! Check your profile for ticket details.", "success")
            return redirect(url_for('profile'))
            
    except Exception as e:
        print(f"Purchase error: {e}")
        flash("An error occurred during purchase. Please try again.", "error")
        return redirect(url_for('checkout'))

# ============== MAINTENANCE (ADMIN ONLY) ==============

@app.route("/maintenance")
@admin_required
def maintenance():
    return render_template("maintenance.html")

@app.route("/imprint")
def imprint():
    return render_template("imprint.html")

# ============== MAINTENANCE CRUD OPERATIONS ==============

@app.route("/persons/new")
@admin_required
def persons_new():
    return render_template("persons_new.html")

@app.route("/persons/create", methods=["POST"])
@admin_required
def persons_create():
    data = {
        "first_name": request.form.get("first_name","").strip(),
        "last_name": request.form.get("last_name","").strip(),
        "email": request.form.get("email") or None,
        "phone": request.form.get("phone") or None,
        "dob": request.form.get("date_of_birth") or None,
    }
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO persons (first_name, last_name, email, phone, date_of_birth)
                VALUES (%s,%s,%s,%s,%s)
            """, (data["first_name"], data["last_name"], data["email"], data["phone"], data["dob"]))
            conn.commit()
        return render_template("feedback.html", title="Create Person", message="Person created successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Person", message=f"Error: {e}")

@app.route("/venues/new")
@admin_required
def venues_new():
    return render_template("venues_new.html")

@app.route("/venues/create", methods=["POST"])
@admin_required
def venues_create():
    v_name = request.form.get("v_name","").strip()
    v_address = request.form.get("v_address") or None
    city = request.form.get("city") or None
    country = request.form.get("country") or None
    capacity = request.form.get("capacity") or None
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO venues (v_name, v_address, city, country, capacity)
                VALUES (%s,%s,%s,%s,%s)
            """, (v_name, v_address, city, country, capacity))
            conn.commit()
        return render_template("feedback.html", title="Create Venue", message="Venue created successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Venue", message=f"Error: {e}")

def get_venues():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT venue_id, CONCAT(v_name,' — ',COALESCE(city,''),', ',COALESCE(country,'')) AS label FROM venues ORDER BY v_name")
        return cur.fetchall()

@app.route("/events/new")
@admin_required
def events_new():
    return render_template("events_new.html", venues=get_venues())

@app.route("/events/create", methods=["POST"])
@admin_required
def events_create():
    title = request.form.get("title","").strip()
    e_description = request.form.get("e_description") or None
    venue_id = request.form.get("venue_id")
    start_time = request.form.get("start_time")
    end_time = request.form.get("end_time") or None
    e_status = request.form.get("e_status","scheduled")
    genre = request.form.get("genre") or None
    is_outdoor = request.form.get("is_outdoor", "0")
    
    # Handle image upload
    image_path = None
    
    # Check if file was uploaded
    if 'event_image' in request.files:
        file = request.files['event_image']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Add timestamp to avoid collisions
            name, ext = os.path.splitext(filename)
            filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_path = filename
    
    # If no file uploaded, check for existing image filename
    if not image_path:
        image_filename = request.form.get("image_filename","").strip()
        if image_filename:
            # Verify the file exists in static/img
            if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], image_filename)):
                image_path = image_filename
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO events (title, e_description, venue_id, start_time, end_time, e_status, image_path)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (title, e_description, venue_id, start_time, end_time, e_status, image_path))
            event_id = cur.lastrowid
            
            # Add concert event details if genre provided
            if genre:
                cur.execute("""
                    INSERT INTO concert_events (event_id, genre, is_outdoor)
                    VALUES (%s, %s, %s)
                """, (event_id, genre, is_outdoor))
            
            conn.commit()
        
        message = "Event created successfully."
        if image_path:
            message += f" Image: {image_path}"
        return render_template("feedback.html", title="Create Event", message=message)
    except Exception as e:
        return render_template("feedback.html", title="Create Event", message=f"Error: {e}")

def get_events():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT event_id, CONCAT(title,' — ', DATE_FORMAT(start_time,'%Y-%m-%d %H:%i')) AS label
          FROM events ORDER BY start_time DESC
        """)
        return cur.fetchall()

def get_seats():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT s.seat_id,
                 CONCAT(COALESCE(s.seat_section,''),'-',COALESCE(s.row_label,''),'-',COALESCE(s.seat_number,''),' @ ',v.v_name) AS label
          FROM seats s JOIN venues v ON v.venue_id = s.venue_id
          ORDER BY v.v_name, s.seat_section, s.row_label, s.seat_number
        """)
        return cur.fetchall()

@app.route("/tickets/new")
@admin_required
def tickets_new():
    return render_template("tickets_new.html", events=get_events(), seats=get_seats())

@app.route("/tickets/create", methods=["POST"])
@admin_required
def tickets_create():
    event_id = request.form.get("event_id")
    seat_id = request.form.get("seat_id") or None
    face_value = request.form.get("face_value")
    currency = request.form.get("currency","EUR")
    ticket_status = request.form.get("ticket_status","available")
    issued_at = request.form.get("issued_at") or None
    ticket_type = request.form.get("ticket_type", "general")
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            # Create the base ticket
            cur.execute("""
              INSERT INTO tickets (event_id, seat_id, face_value, currency, ticket_status, issued_at)
              VALUES (%s,%s,%s,%s,%s,%s)
            """, (event_id, seat_id, face_value, currency, ticket_status, issued_at))
            ticket_id = cur.lastrowid
            
            # Create type-specific ticket entry
            if ticket_type == "vip":
                vip_level = request.form.get("vip_level", "Gold")
                vip_perks = request.form.get("vip_perks") or None
                lounge_access = request.form.get("lounge_access", "1")
                
                cur.execute("""
                    INSERT INTO vip_tickets (ticket_id, perks, lounge_access, vip_level)
                    VALUES (%s, %s, %s, %s)
                """, (ticket_id, vip_perks, lounge_access, vip_level))
            else:  # general or seat
                refundable = request.form.get("refundable", "1")
                refund_deadline = request.form.get("refund_deadline") or None
                
                cur.execute("""
                    INSERT INTO regular_tickets (ticket_id, refundable, refund_deadline)
                    VALUES (%s, %s, %s)
                """, (ticket_id, refundable, refund_deadline))
            
            conn.commit()
        return render_template("feedback.html", title="Create Ticket", 
                             message=f"{ticket_type.upper()} ticket created successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Ticket", message=f"Error: {e}")

def get_customers_for_dropdown():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT c.person_id,
                 CONCAT(p.first_name,' ',p.last_name,' — ',COALESCE(p.email,'no email')) AS label
          FROM customers c JOIN persons p ON p.person_id=c.person_id
          ORDER BY p.last_name, p.first_name
        """)
        return cur.fetchall()

@app.route("/purchases/new")
@admin_required
def purchases_new():
    return render_template("purchases_new.html", customers=get_customers_for_dropdown())

@app.route("/purchases/create", methods=["POST"])
@admin_required
def purchases_create():
    customer_id = request.form.get("customer_id")
    purchase_time = request.form.get("purchase_time") or None
    total_amount = request.form.get("total_amount")
    purch_status = request.form.get("purch_status","pending")
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO purchases (customer_id, purchase_time, total_amount, purch_status)
              VALUES (%s,%s,%s,%s)
            """, (customer_id, purchase_time, total_amount, purch_status))
            conn.commit()
        return render_template("feedback.html", title="Create Purchase", message="Purchase created successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Purchase", message=f"Error: {e}")

def get_purchases_for_dropdown():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT purchase_id,
                 CONCAT('#',purchase_id,' — ',DATE_FORMAT(purchase_time,'%Y-%m-%d %H:%i'),' — €',total_amount) AS label
          FROM purchases ORDER BY purchase_time DESC
        """)
        return cur.fetchall()

@app.route("/payments/new")
@admin_required
def payments_new():
    return render_template("payments_new.html", purchases=get_purchases_for_dropdown())

@app.route("/payments/create", methods=["POST"])
@admin_required
def payments_create():
    purchase_id = request.form.get("purchase_id")
    amount = request.form.get("amount")
    method = request.form.get("method","card")
    transaction_ref = request.form.get("transaction_ref") or None
    paid_at = request.form.get("paid_at") or None
    payment_status = request.form.get("payment_status","ok")
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO payments (purchase_id, amount, method, transaction_ref, paid_at, payment_status)
              VALUES (%s,%s,%s,%s,%s,%s)
            """, (purchase_id, amount, method, transaction_ref, paid_at, payment_status))
            conn.commit()
        return render_template("feedback.html", title="Create Payment", message="Payment recorded successfully.")
    except Exception as e:
        return render_template("feedback.html", title="Create Payment", message=f"Error: {e}")

def get_persons_for_dropdown():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT person_id, CONCAT(first_name,' ',last_name,' — ',COALESCE(email,'no email')) AS label
          FROM persons ORDER BY last_name, first_name
        """)
        return cur.fetchall()

@app.route("/event_organizers/new")
@admin_required
def event_organizers_new():
    return render_template("event_organizers_new.html", events=get_events(), persons=get_persons_for_dropdown())

@app.route("/event_organizers/create", methods=["POST"])
@admin_required
def event_organizers_create():
    event_id = request.form.get("event_id")
    person_id = request.form.get("person_id")
    person_role = request.form.get("person_role") or None
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO event_organizers (event_id, person_id, person_role)
              VALUES (%s,%s,%s)
            """, (event_id, person_id, person_role))
            conn.commit()
        return render_template("feedback.html", title="Assign Organizer", message="Organizer assigned.")
    except Exception as e:
        return render_template("feedback.html", title="Assign Organizer", message=f"Error: {e}")

def get_available_tickets():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
          SELECT t.ticket_id,
                 CONCAT('#',t.ticket_id,' — ',e.title,' — ',
                        COALESCE(CONCAT(s.seat_section,'-',s.row_label,'-',s.seat_number),'GENERAL'),
                        ' — €',t.face_value) AS label
          FROM tickets t
          JOIN events e ON e.event_id=t.event_id
          LEFT JOIN seats s ON s.seat_id=t.seat_id
          WHERE NOT EXISTS (SELECT 1 FROM purchase_items pi WHERE pi.ticket_id=t.ticket_id)
          ORDER BY e.start_time DESC, t.ticket_id
        """)
        return cur.fetchall()

@app.route("/purchase_items/new")
@admin_required
def purchase_items_new():
    return render_template("purchase_items_new.html",
                           purchases=get_purchases_for_dropdown(),
                           tickets=get_available_tickets())

@app.route("/purchase_items/create", methods=["POST"])
@admin_required
def purchase_items_create():
    purchase_id = request.form.get("purchase_id")
    ticket_id = request.form.get("ticket_id")
    price_paid = request.form.get("price_paid")
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
              INSERT INTO purchase_items (purchase_id, ticket_id, price_paid)
              VALUES (%s,%s,%s)
            """, (purchase_id, ticket_id, price_paid))
            conn.commit()
        return render_template("feedback.html", title="Add Ticket to Purchase", message="Ticket added to purchase.")
    except Exception as e:
        return render_template("feedback.html", title="Add Ticket to Purchase", message=f"Error: {e}")

@app.route("/event-venue/new")
@admin_required
def event_venue_new():
    return render_template("events_venue_new.html", events=get_events(), venues=get_venues())

@app.route("/event-venue/create", methods=["POST"])
@admin_required
def event_venue_create():
    event_id = request.form.get("event_id")
    venue_id = request.form.get("venue_id")
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("UPDATE events SET venue_id=%s WHERE event_id=%s", (venue_id, event_id))
            conn.commit()
        return render_template("feedback.html", title="Link Event ↔ Venue", message="Event venue updated.")
    except Exception as e:
        return render_template("feedback.html", title="Link Event ↔ Venue", message=f"Error: {e}")

# ============== DELETE OPERATIONS ==============

@app.route("/delete")
@admin_required
def delete_main():
    return render_template("delete_main.html")

@app.route("/persons/delete", methods=["GET", "POST"])
@admin_required
def persons_delete():
    if request.method == "POST":
        person_id = request.form.get("person_id")
        try:
            with get_conn() as conn, conn.cursor() as cur:
                # Check if person has purchases
                cur.execute("SELECT COUNT(*) FROM purchases WHERE customer_id = %s", (person_id,))
                purchase_count = cur.fetchone()[0]
                
                if purchase_count > 0:
                    return render_template("feedback.html", title="Delete Person", 
                                         message=f"Cannot delete person: {purchase_count} purchase(s) are linked to this person. Please delete purchases first.")
                
                # Check if person is an organizer
                cur.execute("SELECT COUNT(*) FROM event_organizers WHERE person_id = %s", (person_id,))
                organizer_count = cur.fetchone()[0]
                
                if organizer_count > 0:
                    return render_template("feedback.html", title="Delete Person", 
                                         message=f"Cannot delete person: {organizer_count} event(s) have this person as organizer. Please reassign organizers first.")
                
                cur.execute("DELETE FROM persons WHERE person_id = %s", (person_id,))
                conn.commit()
            return render_template("feedback.html", title="Delete Person", message="Person deleted successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Delete Person", message=f"Error: {e}")
    
    # GET request - show form
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT person_id, CONCAT(first_name, ' ', last_name, ' (', COALESCE(email, 'no email'), ')') AS label
                FROM persons ORDER BY last_name, first_name
            """)
            persons = cur.fetchall()
    except:
        persons = []
    return render_template("delete_form.html", title="Delete Person", items=persons, 
                         item_name="person_id", action_url=url_for('persons_delete'))

@app.route("/venues/delete", methods=["GET", "POST"])
@admin_required
def venues_delete():
    if request.method == "POST":
        venue_id = request.form.get("venue_id")
        try:
            with get_conn() as conn, conn.cursor() as cur:
                # Check if venue has events
                cur.execute("SELECT COUNT(*) FROM events WHERE venue_id = %s", (venue_id,))
                event_count = cur.fetchone()[0]
                
                if event_count > 0:
                    return render_template("feedback.html", title="Delete Venue", 
                                         message=f"Cannot delete venue: {event_count} event(s) are using this venue. Please delete or reassign events first.")
                
                cur.execute("DELETE FROM venues WHERE venue_id = %s", (venue_id,))
                conn.commit()
            return render_template("feedback.html", title="Delete Venue", message="Venue deleted successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Delete Venue", message=f"Error: {e}")
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT venue_id, CONCAT(v_name, ' - ', COALESCE(city, ''), ', ', COALESCE(country, '')) AS label
                FROM venues ORDER BY v_name
            """)
            venues = cur.fetchall()
    except:
        venues = []
    return render_template("delete_form.html", title="Delete Venue", items=venues,
                         item_name="venue_id", action_url=url_for('venues_delete'))

@app.route("/events/delete", methods=["GET", "POST"])
@admin_required
def events_delete():
    if request.method == "POST":
        event_id = request.form.get("event_id")
        try:
            with get_conn() as conn, conn.cursor() as cur:
                # First, get all tickets for this event
                cur.execute("SELECT ticket_id FROM tickets WHERE event_id = %s", (event_id,))
                ticket_ids = [row[0] for row in cur.fetchall()]
                
                if ticket_ids:
                    # Delete purchase_items that reference these tickets
                    cur.execute("DELETE FROM purchase_items WHERE ticket_id IN %s", (tuple(ticket_ids),))
                    
                    # Delete regular_tickets and vip_tickets
                    cur.execute("DELETE FROM regular_tickets WHERE ticket_id IN %s", (tuple(ticket_ids),))
                    cur.execute("DELETE FROM vip_tickets WHERE ticket_id IN %s", (tuple(ticket_ids),))
                    
                    # Delete the tickets themselves
                    cur.execute("DELETE FROM tickets WHERE event_id = %s", (event_id,))
                
                # Delete concert_events if exists
                cur.execute("DELETE FROM concert_events WHERE event_id = %s", (event_id,))
                
                # Finally delete the event
                cur.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
                conn.commit()
            return render_template("feedback.html", title="Delete Event", message="Event and all related data deleted successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Delete Event", message=f"Error: {e}")
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT e.event_id, CONCAT(e.title, ' - ', DATE_FORMAT(e.start_time, '%Y-%m-%d')) AS label
                FROM events e ORDER BY e.start_time DESC
            """)
            events = cur.fetchall()
    except:
        events = []
    return render_template("delete_form.html", title="Delete Event", items=events,
                         item_name="event_id", action_url=url_for('events_delete'))

@app.route("/tickets/delete", methods=["GET", "POST"])
@admin_required
def tickets_delete():
    if request.method == "POST":
        ticket_id = request.form.get("ticket_id")
        try:
            with get_conn() as conn, conn.cursor() as cur:
                # Check if ticket is in purchase_items
                cur.execute("SELECT COUNT(*) FROM purchase_items WHERE ticket_id = %s", (ticket_id,))
                purchase_count = cur.fetchone()[0]
                
                if purchase_count > 0:
                    return render_template("feedback.html", title="Delete Ticket", 
                                         message="Cannot delete ticket: This ticket is part of a purchase. Please delete the purchase first.")
                
                # Delete from regular_tickets and vip_tickets first
                cur.execute("DELETE FROM regular_tickets WHERE ticket_id = %s", (ticket_id,))
                cur.execute("DELETE FROM vip_tickets WHERE ticket_id = %s", (ticket_id,))
                
                # Delete the ticket
                cur.execute("DELETE FROM tickets WHERE ticket_id = %s", (ticket_id,))
                conn.commit()
            return render_template("feedback.html", title="Delete Ticket", message="Ticket deleted successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Delete Ticket", message=f"Error: {e}")
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT t.ticket_id, 
                       CONCAT('#', t.ticket_id, ' - ', e.title, ' - €', t.face_value, ' (', t.ticket_status, ')') AS label
                FROM tickets t
                JOIN events e ON t.event_id = e.event_id
                ORDER BY t.ticket_id DESC
            """)
            tickets = cur.fetchall()
    except:
        tickets = []
    return render_template("delete_form.html", title="Delete Ticket", items=tickets,
                         item_name="ticket_id", action_url=url_for('tickets_delete'))

@app.route("/purchases/delete", methods=["GET", "POST"])
@admin_required
def purchases_delete():
    if request.method == "POST":
        purchase_id = request.form.get("purchase_id")
        try:
            with get_conn() as conn, conn.cursor() as cur:
                # Delete purchase_items first (CASCADE should handle this, but being explicit)
                cur.execute("DELETE FROM purchase_items WHERE purchase_id = %s", (purchase_id,))
                
                # Delete payments for this purchase
                cur.execute("DELETE FROM payments WHERE purchase_id = %s", (purchase_id,))
                
                # Delete the purchase
                cur.execute("DELETE FROM purchases WHERE purchase_id = %s", (purchase_id,))
                conn.commit()
            return render_template("feedback.html", title="Delete Purchase", message="Purchase and all related data deleted successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Delete Purchase", message=f"Error: {e}")
    
    try:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                SELECT p.purchase_id,
                       CONCAT('#', p.purchase_id, ' - €', p.total_amount, ' (', p.purch_status, ') - ',
                              DATE_FORMAT(p.purchase_time, '%Y-%m-%d')) AS label
                FROM purchases p ORDER BY p.purchase_id DESC
            """)
            purchases = cur.fetchall()
    except:
        purchases = []
    return render_template("delete_form.html", title="Delete Purchase", items=purchases,
                         item_name="purchase_id", action_url=url_for('purchases_delete'))

# ============== EDIT OPERATIONS ==============

@app.route("/edit")
@admin_required
def edit_main():
    return render_template("edit_main.html")

@app.route("/persons/edit", methods=["GET", "POST"])
@admin_required
def persons_edit():
    if request.method == "POST":
        person_id = request.form.get("person_id")
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email") or None
        phone = request.form.get("phone") or None
        
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    UPDATE persons 
                    SET first_name = %s, last_name = %s, email = %s, phone = %s
                    WHERE person_id = %s
                """, (first_name, last_name, email, phone, person_id))
                conn.commit()
            return render_template("feedback.html", title="Edit Person", message="Person updated successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Edit Person", message=f"Error: {e}")
    
    # GET request - show selection or edit form
    person_id = request.args.get("id")
    if person_id:
        # Show edit form for specific person
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("SELECT * FROM persons WHERE person_id = %s", (person_id,))
                person = cur.fetchone()
                if not person:
                    flash("Person not found.", "error")
                    return redirect(url_for('persons_edit'))
        except:
            person = None
        return render_template("persons_edit_form.html", person=person)
    else:
        # Show selection list
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT person_id, CONCAT(first_name, ' ', last_name, ' (', COALESCE(email, 'no email'), ')') AS label
                    FROM persons ORDER BY last_name, first_name
                """)
                persons = cur.fetchall()
        except:
            persons = []
        return render_template("edit_select.html", title="Edit Person", items=persons,
                             item_name="person_id", edit_url="persons_edit")

@app.route("/venues/edit", methods=["GET", "POST"])
@admin_required
def venues_edit():
    if request.method == "POST":
        venue_id = request.form.get("venue_id")
        v_name = request.form.get("v_name")
        v_address = request.form.get("v_address") or None
        city = request.form.get("city") or None
        country = request.form.get("country") or None
        capacity = request.form.get("capacity") or None
        
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    UPDATE venues 
                    SET v_name = %s, v_address = %s, city = %s, country = %s, capacity = %s
                    WHERE venue_id = %s
                """, (v_name, v_address, city, country, capacity, venue_id))
                conn.commit()
            return render_template("feedback.html", title="Edit Venue", message="Venue updated successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Edit Venue", message=f"Error: {e}")
    
    venue_id = request.args.get("id")
    if venue_id:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("SELECT * FROM venues WHERE venue_id = %s", (venue_id,))
                venue = cur.fetchone()
                if not venue:
                    flash("Venue not found.", "error")
                    return redirect(url_for('venues_edit'))
        except:
            venue = None
        return render_template("venues_edit_form.html", venue=venue)
    else:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT venue_id, CONCAT(v_name, ' - ', COALESCE(city, ''), ', ', COALESCE(country, '')) AS label
                    FROM venues ORDER BY v_name
                """)
                venues = cur.fetchall()
        except:
            venues = []
        return render_template("edit_select.html", title="Edit Venue", items=venues,
                             item_name="venue_id", edit_url="venues_edit")

@app.route("/events/edit", methods=["GET", "POST"])
@admin_required
def events_edit():
    if request.method == "POST":
        event_id = request.form.get("event_id")
        title = request.form.get("title")
        e_description = request.form.get("e_description") or None
        venue_id = request.form.get("venue_id")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time") or None
        e_status = request.form.get("e_status")
        image_filename = request.form.get("image_filename") or None
        genre = request.form.get("genre") or None
        is_outdoor = request.form.get("is_outdoor", "0")
        
        # Handle image upload
        image_path = image_filename
        if 'event_image' in request.files:
            file = request.files['event_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                name, ext = os.path.splitext(filename)
                filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = filename
        
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    UPDATE events 
                    SET title = %s, e_description = %s, venue_id = %s, start_time = %s, 
                        end_time = %s, e_status = %s, image_path = %s
                    WHERE event_id = %s
                """, (title, e_description, venue_id, start_time, end_time, e_status, image_path, event_id))
                
                # Update concert event details if genre provided
                if genre:
                    cur.execute("""
                        INSERT INTO concert_events (event_id, genre, is_outdoor)
                        VALUES (%s, %s, %s)
                        ON DUPLICATE KEY UPDATE genre = %s, is_outdoor = %s
                    """, (event_id, genre, is_outdoor, genre, is_outdoor))
                
                conn.commit()
            return render_template("feedback.html", title="Edit Event", message="Event updated successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Edit Event", message=f"Error: {e}")
    
    event_id = request.args.get("id")
    if event_id:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT e.*, ce.genre, ce.is_outdoor
                    FROM events e
                    LEFT JOIN concert_events ce ON e.event_id = ce.event_id
                    WHERE e.event_id = %s
                """, (event_id,))
                event = cur.fetchone()
                if not event:
                    flash("Event not found.", "error")
                    return redirect(url_for('events_edit'))
        except:
            event = None
        return render_template("events_edit_form.html", event=event, venues=get_venues())
    else:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT e.event_id, CONCAT(e.title, ' - ', DATE_FORMAT(e.start_time, '%Y-%m-%d')) AS label
                    FROM events e ORDER BY e.start_time DESC
                """)
                events = cur.fetchall()
        except:
            events = []
        return render_template("edit_select.html", title="Edit Event", items=events,
                             item_name="event_id", edit_url="events_edit")

@app.route("/tickets/edit", methods=["GET", "POST"])
@admin_required
def tickets_edit():
    if request.method == "POST":
        ticket_id = request.form.get("ticket_id")
        face_value = request.form.get("face_value")
        ticket_status = request.form.get("ticket_status")
        
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    UPDATE tickets 
                    SET face_value = %s, ticket_status = %s
                    WHERE ticket_id = %s
                """, (face_value, ticket_status, ticket_id))
                conn.commit()
            return render_template("feedback.html", title="Edit Ticket", message="Ticket updated successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Edit Ticket", message=f"Error: {e}")
    
    ticket_id = request.args.get("id")
    if ticket_id:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT t.*, e.title as event_title
                    FROM tickets t
                    JOIN events e ON t.event_id = e.event_id
                    WHERE t.ticket_id = %s
                """, (ticket_id,))
                ticket = cur.fetchone()
                if not ticket:
                    flash("Ticket not found.", "error")
                    return redirect(url_for('tickets_edit'))
        except:
            ticket = None
        return render_template("tickets_edit_form.html", ticket=ticket)
    else:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT t.ticket_id, 
                           CONCAT('#', t.ticket_id, ' - ', e.title, ' - €', t.face_value, ' (', t.ticket_status, ')') AS label
                    FROM tickets t
                    JOIN events e ON t.event_id = e.event_id
                    ORDER BY t.ticket_id DESC
                """)
                tickets = cur.fetchall()
        except:
            tickets = []
        return render_template("edit_select.html", title="Edit Ticket", items=tickets,
                             item_name="ticket_id", edit_url="tickets_edit")

@app.route("/purchases/edit", methods=["GET", "POST"])
@admin_required
def purchases_edit():
    if request.method == "POST":
        purchase_id = request.form.get("purchase_id")
        total_amount = request.form.get("total_amount")
        purch_status = request.form.get("purch_status")
        
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    UPDATE purchases 
                    SET total_amount = %s, purch_status = %s
                    WHERE purchase_id = %s
                """, (total_amount, purch_status, purchase_id))
                conn.commit()
            return render_template("feedback.html", title="Edit Purchase", message="Purchase updated successfully.")
        except Exception as e:
            return render_template("feedback.html", title="Edit Purchase", message=f"Error: {e}")
    
    purchase_id = request.args.get("id")
    if purchase_id:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT p.*, CONCAT(per.first_name, ' ', per.last_name) as customer_name
                    FROM purchases p
                    JOIN customers c ON p.customer_id = c.person_id
                    JOIN persons per ON c.person_id = per.person_id
                    WHERE p.purchase_id = %s
                """, (purchase_id,))
                purchase = cur.fetchone()
                if not purchase:
                    flash("Purchase not found.", "error")
                    return redirect(url_for('purchases_edit'))
        except:
            purchase = None
        return render_template("purchases_edit_form.html", purchase=purchase)
    else:
        try:
            with get_conn() as conn, conn.cursor() as cur:
                cur.execute("""
                    SELECT p.purchase_id,
                           CONCAT('#', p.purchase_id, ' - €', p.total_amount, ' (', p.purch_status, ') - ',
                                  DATE_FORMAT(p.purchase_time, '%Y-%m-%d')) AS label
                    FROM purchases p ORDER BY p.purchase_id DESC
                """)
                purchases = cur.fetchall()
        except:
            purchases = []
        return render_template("edit_select.html", title="Edit Purchase", items=purchases,
                             item_name="purchase_id", edit_url="purchases_edit")

if __name__ == '__main__':
    app.run(debug=True, port=5001)
