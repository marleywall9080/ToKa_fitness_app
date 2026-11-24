# code for login system is from geek for geeks, https://www.geeksforgeeks.org/python/how-to-add-authentication-to-your-app-with-flask-login/
# imports required for the code
from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

font_size = "medium"

#Start of code from geek for geeks, comments may be scarce and not fully correct

app = Flask(__name__) # intialising flask and setting up the requirements for sqlalchemy and login
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.sqlite"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "supersecretkey"

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
    if request.method == "POST": # gets the user's username and password
        username = request.form.get("username")
        password = request.form.get("password")

        if Users.query.filter_by(username=username).first(): # checks if it is already taken
            return render_template("sign_up.html", error="Username already taken!")
        elif username == "DROP TABLE" or username == "1=1": # code by me to stop some simple sql injection methods i could think of
            return render_template("sign_up.html", error="Username is not valid")

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256") # encrypts the password

        new_user = Users(username=username, password=hashed_password)
        db.session.add(new_user) # writes down the new username and encrypted password to a database
        db.session.commit()

        return redirect(url_for("login")) # takes the user to the login page
    
    return render_template("sign_up.html")

# Login route
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST": # gets the users username and password
        username = request.form.get("username")
        password = request.form.get("password")

        user = Users.query.filter_by(username=username).first() # checks if the username exists in the database

        if user and check_password_hash(user.password, password): # checks if the password matches to the username
            login_user(user)
            return redirect(url_for("home")) # takes the user to the homepage
        else:
            return render_template("login.html", error="Invalid username or password")

    return render_template("login.html")

# Logout route
@app.route("/logout")
@login_required # means a user is required to be logged in to use this
def logout():
    logout_user() # logs out the user
    return redirect(url_for("login"))

# end of code from geek for geeks

tier = "standard"

# home page
@app.route("/home")
@login_required
def home():
    global tier
    if current_user.username == "admin":
        tier = "premium"
    conn = sqlite3.connect("advice.db") # connects to the database
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row
    cursor.execute("SELECT  * FROM advice ORDER BY RANDOM() LIMIT 1") # code from geek for geeks, randomly scrambles the order of data in the database and then takes the first one
    records = cursor.fetchall() # sets up a variable with all the selected data in it
    cursor.execute("SELECT * FROM videos ORDER BY RANDOM() LIMIT 1")
    videos = cursor.fetchall()
    return render_template("home.html", username=current_user.username, records = records, videos=videos, font_size=font_size) # renders the html page and sends the selected data

# advice page
@app.route("/advice")
@login_required
def advice():
    conn = sqlite3.connect("advice.db") # connects to the database
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row
    cursor.execute("SELECT * FROM advice") # selects all items from advice
    records = cursor.fetchall()  # puts all the items from advice into a list
    conn.close()
    return render_template("advice.html", records=records, font_size=font_size, username=current_user.username) # renders the html page with the required data

# filter system
@app.route("/filter", methods=["POST", "GET"])
@login_required
def filter():
    conn = sqlite3.connect("advice.db")
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row
    if request.method == "POST":
        filter = request.form.get("filter")
        if filter == "*": # this is if the user selects all
            return redirect(url_for("advice")) # directly redirects to standard advice page since that already shows all
        else: # this is for what else the user could input, since the filter selection is from a dropdown menu there is only predetermined options which line up with options from adding the advice
            cursor.execute("SELECT * FROM advice WHERE advice_type = ?", (filter,)) # selects all the data in advice where the advice type matches the filter
            records = cursor.fetchall() 
            conn.close() # closes the database
            return render_template("advice.html", records=records, font_size=font_size, username=current_user.username) # renders the advice page with the new data from the table

# posting advice page
@app.route("/create_advice", methods=["GET", "POST"])
@login_required
def create_advice():
    if request.method == "POST":
        conn = sqlite3.connect("advice.db")
        cursor = conn.cursor()
        advice = request.form.get("advice") # gets the advice from a form on the html page
        advice_type = request.form.get("type")

        cursor.execute("INSERT INTO advice (advice, advice_type, user) VALUES (?, ?, ?)", (advice, advice_type, current_user.username)) # puts the data into the database
        conn.commit()
        conn.close()
        return redirect(url_for("advice")) # takes user to the advice page
    return render_template("create_advice.html", font_size=font_size) # renders the html page

# training page
@app.route("/training")
@login_required
def training():
    conn = sqlite3.connect("advice.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM training WHERE user=?",
                (current_user.username,)) # only takes the data from the database where the recorded username is the same as the one currently logged in so people don't see other peoples workout plans
    records = cursor.fetchall()
    return render_template("training.html", records=records, font_size=font_size)

# creating a training plan page
@app.route("/training_plan", methods=["GET", "POST"])
@login_required
def training_plan():
    if request.method == "POST":
        conn = sqlite3.connect("advice.db")
        cursor = conn.cursor()
        exercise = request.form.get("exercise")
        workout_type = request.form.get("type")
        sets = request.form.get("sets")
        reps = request.form.get("reps")

        cursor.execute("INSERT INTO training (exercise, workout_type, sets, reps, user) VALUES (?, ?, ?, ?, ?)", (exercise, workout_type, sets, reps, current_user.username)) # records the username of the person currently logged in so that it can filter out other peoples workout plans later
        conn.commit()
        return redirect(url_for("training"))
    return render_template("training_plan.html", font_size=font_size)

@app.route("/personal_trainer")
def personal_trainer():
    return "pretend this is ToKa Fitness' site for booking personal trainers" # i have not created a page for this as this is one of ToKa fitness' other services, and so it is only needed to draw attention to them

# videos page
@app.route("/videos")
@login_required
def videos():
    conn = sqlite3.connect("advice.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM videos") # selects all data from the videos table
    records = cursor.fetchall()
    return render_template("videos.html", records=records, font_size=font_size, user=current_user.username)

# add videos page
@app.route("/add_videos", methods=["POST", "GET"])
@login_required
def add_videos():
    if current_user.username == "admin": # checks if the current logged in user is called admin
        if request.method == "POST": # if so page works like normal
            conn = sqlite3.connect("advice.db")
            cursor = conn.cursor()

            video_link = request.form.get("video_link")
            type = request.form.get("type")

            cursor.execute("INSERT INTO videos (video_link, advice_type) VALUES (?, ?)", (video_link, type))
            conn.commit()
            return redirect(url_for("videos"))
        return render_template("add_videos.html", font_size=font_size)
    else:
        return redirect(url_for("home")) # if not they are returned to the home page

# diet page
@app.route("/diet")
@login_required
def diet():
        calories = 0 # intializes the calories variable
        conn = sqlite3.connect("advice.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM diets WHERE user=?",
                    (current_user.username,)) # gets all items in the table where the username is the same as the currently logged in user
        records = cursor.fetchall()
        for r in records:
            calories += r[3] # counts up all the users calories
        return render_template("diet.html", records=records, calories=calories, font_size=font_size, user=current_user.username)

# diet plan page
@app.route("/diet_plan", methods=["POST", "GET"])
@login_required
def diet_plan():
    if request.method == "POST":
        conn = sqlite3.connect("advice.db")
        cursor = conn.cursor()
        food = request.form.get("food")
        meal = request.form.get("meal")
        calories = request.form.get("calories")

        cursor.execute("INSERT INTO diets (food, meal, calories, user) VALUES (?, ?, ?, ?)",
                    (food, meal, calories, current_user.username))
        conn.commit()
        return redirect(url_for("diet"))
    return render_template("diet_plan.html", font_size=font_size)

# settings page
@app.route("/settings", methods=["POST", "GET"])
@login_required
def settings():
    return render_template("settings.html", font_size=font_size, user=current_user.username, tier=tier)

# font size function
@app.route("/change_font", methods=["POST", "GET"], endpoint="change_font")
def change_font():
    if request.method == "POST":
        global font_size # makes the variable font_size global
        font_size = request.form.get("font_size")
        return render_template("settings.html", font_size=font_size, user=current_user.username) # added "font_size=font_size" to every return statement so that it can be used to change the font size on every page

# tiers function
@app.route("/tier", methods=["POST", "GET"], endpoint="tier")
@login_required
def tier():
    if request.method == "POST":
        if current_user.username == "admin":
            return "You can't downgrade as an admin"
        global tier
        if tier == "premium":
            tier = "standard"
            return render_template("downgrade.html", font_size=font_size)
        else:
            tier = "premium"
            return render_template("upgrade.html", font_size=font_size)

# delete function
@app.route("/delete", methods=["POST", "GET"], endpoint="delete")
@login_required
def delete():
    if request.method == "POST":
        conn = sqlite3.connect("advice.db")
        cursor = conn.cursor()
        table = request.form.get("table") # gets all required data to remove an item from a table
        id = request.form.get("id")
        delete = request.form.get("delete")
        url = request.form.get("url")

        cursor.execute(f"DELETE FROM {table} WHERE {id} = ?", (delete,)) # deletes the item from the table
        conn.commit()
        return redirect(url_for(url)) # redirects to the page that the user was already on

# start
@app.route("/")
def index(): # simple start page for people who aren't signed in
    return render_template("index.html")

if __name__ == "__main__": # runs the app
    app.run(debug=True)
