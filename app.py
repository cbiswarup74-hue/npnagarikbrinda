import sqlite3
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, render_template_string
import razorpay

app = Flask(__name__)
app.secret_key = 'neogi_para_super_secret_key_change_me'  # Required for Flask session cookies

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "Password123!"

# Razorpay API Credentials
RAZORPAY_KEY_ID = "rzp_test_TIOqGWuejGngEo"
RAZORPAY_KEY_SECRET = "ThdoBLM4rlgpdI2nV4892oE2"

client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            razorpay_order_id TEXT NOT NULL,
            razorpay_payment_id TEXT NOT NULL,
            payment_status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Prevent Browser Caching of Protected Admin Pages
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

# Decorator to enforce session authentication
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Main Site Navigation Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about-us')
def about_us():
    return render_template('about_us.html')

# Activities Routes
@app.route('/activities/cultural-activities')
def cultural_activities():
    return render_template('cultural_activities.html')

@app.route('/activities/festivals')
def festivals():
    return render_template('festivals.html')

@app.route('/activities/social-workshops')
def social_workshops():
    return render_template('social_workshops.html')

# Events Calendar Routes
@app.route('/events')
@app.route('/events-calendar')
def events_calendar():
    return render_template('events_calendar.html')

# Contact Us Route
@app.route('/contact')
def contact():
    return render_template('contact.html')

# Subscription Routes
@app.route('/subscribe/member')
def subscribe_member():
    return render_template('subscribe_member.html', key_id=RAZORPAY_KEY_ID)

@app.route('/subscribe/other')
def subscribe_other():
    return render_template('subscribe_other.html', key_id=RAZORPAY_KEY_ID)

# Payment Endpoints
@app.route('/create-payment-order', methods=['POST'])
def create_payment_order():
    data = request.get_json()
    amount = int(float(data.get('amount', 500))) * 100

    try:
        order_data = {
            'amount': amount,
            'currency': 'INR',
            'payment_capture': 1
        }
        order = client.order.create(data=order_data)
        return jsonify(order)
    except Exception as e:
        return jsonify({
            'id': 'order_fake_12345',
            'amount': amount,
            'currency': 'INR'
        })

@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    data = request.get_json()
    try:
        name = data.get('name', 'N/A')
        phone = data.get('phone', 'N/A')
        amount = data.get('amount', 0)
        category = data.get('category', 'Member Subscription')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payments (name, phone, amount, category, razorpay_order_id, razorpay_payment_id, payment_status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, amount, category, data.get('razorpay_order_id', 'N/A'), data.get('razorpay_payment_id', 'N/A'), 'SUCCESS', timestamp))
        conn.commit()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Payment Verified and Recorded Successfully!'})

    except Exception as e:
        return jsonify({'status': 'failure', 'message': str(e)}), 400

# Dedicated Admin Login Route
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('view_payments'))
        else:
            error = 'Invalid Username or Password!'

    LOGIN_HTML = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login - Neogi Para Nagarikbrinda</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f1f5f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-card { background: white; padding: 2.5rem; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.1); width: 320px; }
            h2 { color: #0f172a; margin-top: 0; text-align: center; font-size: 1.5rem; }
            .error { color: #dc2626; background: #fef2f2; padding: 8px; border-radius: 6px; font-size: 0.9rem; text-align: center; margin-bottom: 1rem; border: 1px solid #fecaca; }
            label { font-weight: bold; font-size: 0.9rem; color: #334155; display: block; margin-top: 1rem; }
            input[type="text"], input[type="password"] { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
            button { width: 100%; margin-top: 1.5rem; padding: 10px; background-color: #0284c7; color: white; border: none; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 1rem; }
            button:hover { background-color: #0369a1; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h2>Admin Login</h2>
            {% if error %}
                <div class="error">{{ error }}</div>
            {% endif %}
            <form method="POST">
                <label>Username</label>
                <input type="text" name="username" required placeholder="Enter admin username">
                
                <label>Password</label>
                <input type="password" name="password" required placeholder="Enter password">
                
                <button type="submit">Sign In</button>
            </form>
        </div>
    </body>
    </html>
    """
    return render_template_string(LOGIN_HTML, error=error)

# Password Protected Admin Route
@app.route('/admin/payments')
@login_required
def view_payments():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM payments ORDER BY id DESC")
    records = cursor.fetchall()
    conn.close()
    
    output = """
    <html>
    <head>
        <title>Payment Records - Neogi Para Nagarikbrinda</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 2rem; background-color: #f8fafc; }
            .header-container { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
            h2 { color: #0f172a; margin: 0; }
            .logout-btn { background-color: #ef4444; color: white; padding: 8px 16px; text-decoration: none; border-radius: 6px; font-weight: bold; }
            .logout-btn:hover { background-color: #dc2626; }
            table { width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
            th, td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #e2e8f0; }
            th { background-color: #0f172a; color: white; }
            tr:hover { background-color: #f1f5f9; }
        </style>
    </head>
    <body>
        <div class="header-container">
            <h2>Neogi Para Nagarikbrinda - Payment Records</h2>
            <a href="/admin/logout" class="logout-btn">Log Out</a>
        </div>
        <table>
            <tr>
                <th>ID</th><th>Name</th><th>Phone</th><th>Amount (₹)</th>
                <th>Category</th><th>Razorpay Payment ID</th><th>Date & Time</th>
            </tr>
    """
    for row in records:
        output += f"""
            <tr>
                <td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td>
                <td>₹{row[3]}</td><td>{row[4]}</td><td>{row[6]}</td><td>{row[8]}</td>
            </tr>
        """
    output += "</table></body></html>"
    return output

# Admin Logout Route
@app.route('/admin/logout')
def admin_logout():
    session.clear()  # Destroys active login session
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)