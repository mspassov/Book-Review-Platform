import os
import requests

from flask import Flask, session, render_template, url_for, request, jsonify
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

	session["user"] = username

	row = db.execute("SELECT * FROM accounts where username = :username and password = :password", {"username": username, "password": password}).rowcount
	db.commit()

	if row == 1:
		return render_template("dashboard.html", displayName = username)
	else:
		return render_template("login.html", row=0)

@app.route("/dashboard")
def dashboard():
	return render_template("dashboard.html")


@app.route("/search", methods=["POST"])
def search():
	check = 0
	search = request.form.get("search")

	if search == "":
		#error
		check+=1
		return render_template("dashboard.html", check=1)

	elif search[0].isdigit() == True:
		#isbn search
		results = db.execute("SELECT * from books where isbn like :search ", {"search":'%' + search + '%'})
		row = db.execute("SELECT * from books where isbn like :search ", {"search":'%' + search + '%'}).rowcount
		if row == 0:
			return render_template("dashboard.html", check=4)

		return render_template("dashboard.html", results=results, check=2)

	else:
		#title and author search
		authorResults = db.execute("SELECT * from books where author like :search ", {"search":'%' + search + '%'})
		titleResults = db.execute("SELECT * from books where title like :search ", {"search":'%' + search + '%'})
		row = db.execute("SELECT * from books where title like :search ", {"search":'%' + search + '%'}).rowcount + db.execute("SELECT * from books where author like :search ", {"search":'%' + search + '%'}).rowcount
		if row == 0:
			return render_template("dashboard.html", check=4)

		return render_template("dashboard.html", check=3, results1=titleResults, results2=authorResults)
	

@app.route("/<string:bookName>", methods=["GET", "POST"])
def reviews(bookName):

	content = db.execute("SELECT * from books where title=:bookName", {"bookName": bookName})
	passedContent = db.execute("SELECT * from books where title=:bookName", {"bookName": bookName})
	isbnKey = ""
	for i in content:
		isbnKey = i.isbn
	
	imageURL="http://covers.openlibrary.org/b/isbn/"+isbnKey+"-M.jpg"

	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "3a3uMt1q8uLsCdlWggCzA", "isbns": isbnKey})
	res = res.json()
	avgRating = res["books"][0]["average_rating"]
	numRating = res["books"][0]["work_ratings_count"]

	rowCheck = 0
	if request.method == "POST":
		score = request.form.get("score")
		rev = request.form.get("reviewPosted")
		username = session["user"]
		isbn = session["isbn"]

		rowCheck = db.execute("SELECT * from reviews where username=:name and isbn=:isbn", {"name": username, "isbn":isbn}).rowcount
		db.commit()

		if rowCheck == 0:
			db.execute("INSERT into reviews (username, isbn, review, rating) VALUES (:username, :isbn, :review, :rating)", 
				{"username": username, "isbn": isbn, "review": rev, "rating": score})
			db.commit()

	#display the current reviews
	reviewsDB = db.execute("SELECT * from reviews where isbn=:isbnK", {"isbnK": isbnKey})
	db.commit()
	session["isbn"] = isbnKey


	return render_template("reviews.html", results=passedContent, imageURL=imageURL, avgRating=avgRating, 
		numRating=numRating, reviewsDB=reviewsDB, block=rowCheck)


@app.route("/api/<string:isbn>")
def book_api(isbn):

	book = db.execute("SELECT * from books where isbn=:isbn", {"isbn":isbn})
	bookRow = db.execute("SELECT * from books where isbn=:isbn", {"isbn":isbn}).rowcount

	if bookRow == 0:
		return jsonify({"error": "invalid book ISBN"}), 404

	else:
		for row in book:
			title = row.title
			author = row.author
			year = row.year

			res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "3a3uMt1q8uLsCdlWggCzA", "isbns": isbn})
			res = res.json()
			avgRating = res["books"][0]["average_rating"]
			numRating = res["books"][0]["work_ratings_count"]

			return jsonify({
					"title": title,
					"author": author,
					"year": year,
					"isbn": isbn,
					"review_count": numRating,
					"average_score": avgRating
				})
			

if __name__ == "__main__":
	app.run(debug=True)
