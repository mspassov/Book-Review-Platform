import os
import requests

from flask import Flask, session, render_template, url_for, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

isbn = "9781632168146"

res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "3a3uMt1q8uLsCdlWggCzA", "isbns": isbn})
res = res.json()
print(res["books"][0]["average_rating"])