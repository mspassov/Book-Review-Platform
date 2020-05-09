import os
import requests

from flask import Flask, session, render_template, url_for, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return render_template("index.html", title = "Home")

@app.route("/register")
def register():
	return render_template("register.html")

@app.route("/regComplete", methods=["POST"])
def regComplete():

	uname = request.form.get("username")
	passw = request.form.get("password")
	confirmPass = request.form.get("cpassword")

	if passw != confirmPass:
		return render_template("register.html", message="passwords do not match")

	if passw == '' or uname == '':
		return render_template("register.html", message="you have not completed all the fields")

	try:
		db.execute("INSERT INTO accounts (username, password) VALUES (:uname, :passw)", {"uname": uname, "passw": passw})
		db.commit()
		return render_template("index.html", check = "registered")
	except:
		return render_template("register.html", message="username is already taken, please try again")

@app.route("/login")
def login():
	return render_template("login.html")

@app.route("/account", methods=["POST"])
def account():
	username = request.form.get("username")
	password = request.form.get("password")
	row = db.execute("SELECT * FROM accounts where username = :username and password = :password", {"username": username, "password": password}).rowcount
	if row == 1:
		var = "signed in"
		return f"Welcome back! {var}"
	else:
		return render_template("login.html", row=0)
	
	


