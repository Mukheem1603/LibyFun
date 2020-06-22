import os
import requests
import time
from flask import Flask, session,render_template,request,redirect,url_for,flash,make_response,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


app = Flask(__name__)
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
# res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "qQB2Uiw9My1Hrlov379BQ", "isbns": "9781632168146"})
# print(res.json())
# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



@app.route("/")
def index():
    if request.cookies.get('username'):
        return redirect(url_for('login'))
    if request.cookies.get('error'):
        return render_template("register.html",error=request.cookies.get('error'))
    return render_template("register.html")

@app.route("/register",methods=["POST","GET"])
def register():
    if request.cookies.get('username'):
        return render_template("home.html",user=request.cookies.get('username'))
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if db.execute("SELECT * from users WHERE username= :u AND password= :p",{"u":username,"p":password}).rowcount == 1 :
            print("User already exists,Log In")
            r1 = make_response(redirect(url_for('loginpage')))
            r1.set_cookie('error','User already exists,Log In',max_age=10) 
            return r1
        elif db.execute("SELECT * from users WHERE username= :u",{"u":username}).rowcount == 1:
            print("Username already exists, try using another one 🤔")
            r5 =make_response(redirect(url_for('index')))
            r5.set_cookie('error','Username already exists, try using another one 🤔',max_age=10)
            return r5 
        else :
            db.execute("INSERT INTO users (username,password) VALUES (:username, :password)",{"username":username,"password":password})
            db.commit()
            print("Registration Successful!!!,now login to the world of books")
            r2 = make_response(redirect(url_for('loginpage')))
            r2.set_cookie('error','Registration Successful!!!,now login to the world of books',max_age=10) 
            return r2

@app.route("/login",methods=["POST","GET"])
def loginpage():
    if request.cookies.get('username'):
        return redirect(url_for('login'))
    if request.method == "GET" and request.cookies.get('error'):
        err = request.cookies.get('error')
        return render_template("login.html",error=err)
    else:
        re=make_response(render_template("login.html"))
        re.set_cookie('error','',expires=0)
        return re

    
    

@app.route("/home",methods=["POST","GET"])
def login():
    if request.cookies.get('username'):
        return render_template("home.html",user=request.cookies.get('username'),error=request.cookies.get('error'))
    if request.method == "POST":
        UName = request.form.get("user")
        Pwd = request.form.get("pass")
        if db.execute("SELECT * from users WHERE username= :u AND password= :p",{"u":UName,"p":Pwd}).rowcount == 1 :
            print("Successful login")
            resp=make_response(render_template("home.html",user=UName))
            resp.set_cookie('username',UName)
            return resp
        else :
            print("Incorrect username/password, Try again")
            r3 =make_response(redirect(url_for('loginpage')))
            r3.set_cookie('error','Incorrect username/password, Try again 😓',max_age=10) 
            return r3
    if request.method == "GET":
        return redirect(url_for('index'))

@app.route("/search",methods=["POST"])
def search():
    if request.cookies.get('username') == None:
        render_template(url_for('index'))
    qry = request.form.get("query")
    query = "%" + qry + "%"
    books = db.execute("SELECT * FROM books WHERE title ILIKE :q OR author ILIKE :q OR isbn ILIKE :q",{"q": query}).fetchall()
    print(books)
    if books :
        u=request.cookies.get('username')
        return render_template("results.html",books=books,user=u)
    else :
        r5 =make_response(redirect(url_for('login')))
        r5.set_cookie('error','No matches found 😓',max_age=10) 
        return r5

@app.route("/book/<isbn>", methods=['GET','POST'])
def bookpage(isbn):
    API="qQB2Uiw9My1Hrlov379BQ"
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": API, "isbns": isbn})
    if res :
        print(res.json())
        goodinfo = res.json()
        scratch = goodinfo["books"]
        reviews_count = scratch[0]["work_ratings_count"]
        average_rating = scratch[0]["average_rating"]
        u = request.cookies.get('username')
        if db.execute("SELECT * FROM bookreviews WHERE userrev=:u AND isbn=:i",{"u":u,"i":isbn}).rowcount > 0:
            display = False
        else :
            display = True
        if request.method == "POST" and db.execute("SELECT * FROM bookreviews WHERE userrev=:u AND isbn=:i",{"u":u,"i":isbn}).rowcount == 0:
            rating = request.form.get("rating")
            reviews = request.form.get("review")
            ts = time.gmtime()
            timestamp = time.strftime("%x %X", ts)
            db.execute("INSERT INTO bookreviews (isbn, userrev, review, time) VALUES (:i, :u, :r, :t)",{"i":isbn,"u":u,"r":reviews,"t":timestamp})
            db.commit()
        if db.execute("SELECT * FROM bookreviews WHERE userrev=:u AND isbn=:i",{"u":u,"i":isbn}).rowcount > 0:
            display = False
        else :
            display = True
        books = db.execute("SELECT * from books WHERE isbn = :i",{"i":isbn}).fetchall()
        reviews = db.execute("SELECT * from bookreviews WHERE isbn=:i",{"i":isbn}).fetchall()
        return render_template("book.html",books=books,ar=average_rating,count=reviews_count,reviews=reviews,display=display,isbn=isbn)
    else :
        r4 =make_response(redirect(url_for('login')))
        r4.set_cookie('error','Incorrect isbn 😓',max_age=10) 
        return r4



@app.route("/logout")
def logout():
    res=make_response(render_template("logout.html"))
    res.set_cookie('username','',expires=0)
    return res 


@app.route("/api/<isbn>",methods=['GET'])
def api(isbn):
    books=db.execute("SELECT * FROM books WHERE isbn= :i",{"i":isbn}).fetchone()
    if books :
        API="qQB2Uiw9My1Hrlov379BQ"
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": API, "isbns": isbn})
        if res :
            print(res.json())
            goodinfo = res.json()
            scratch = goodinfo["books"]
            reviews_count = scratch[0]["work_ratings_count"]
            average_rating = scratch[0]["average_rating"]
            bjson = [
                {
                    "title": books['title'],
                    "author": books['author'],
                    "year": books['year'],
                    "isbn": books['isbn'],
                    "review_count": reviews_count,
                    "average_score": average_rating
                }
             ]
            return jsonify(bjson)
        else :
            return "ERROR",404
    else :
        return "ERROR",404
        

       