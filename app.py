# code for login system is from geek for geeks, https://www.geeksforgeeks.org/python/how-to-add-authentication-to-your-app-with-flask-login/
from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"

#Start of code from geek for geeks

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# User model
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

# Create database
with app.app_context():
    db.create_all()

# Load user for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Register route
@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if Users.query.filter_by(username=username).first():
            return render_template("sign_up.html", error="Username already taken!")

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = Users(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))
    
    return render_template("sign_up.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# end of code from geek for geeks

@app.route("/home")
@login_required
def home():
    conn = sqlite3.connect("advice.db")
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row
    cursor.execute("SELECT  * FROM advice ORDER BY RANDOM() LIMIT 1") # code from geek for geeks
    record = cursor.fetchall()
    return render_template("home.html", username=current_user.username)

@app.route("/advice")
@login_required
def advice():
    conn = sqlite3.connect("advice.db")
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row
    cursor.execute("SELECT * FROM advice")
    records = cursor.fetchall()
    conn.close()
    return render_template("advice.html", records=records)

@app.route("/create_advice", methods=["GET", "POST"])
@login_required
def create_advice():
    if request.method == "POST":
        conn = sqlite3.connect("advice.db")
        cursor = conn.cursor()
        advice = request.form.get("advice")
        advice_type = request.form.get("type")

        cursor.execute("INSERT INTO advice (advice, advice_type, user) VALUES (?, ?, ?)", (advice, advice_type, current_user.username))
        conn.commit()
        conn.close()
        return redirect(url_for("advice"))
    return render_template("create_advice.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
