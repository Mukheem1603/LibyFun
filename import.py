import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

os.environ["DATABASE_URL"]="postgres://suzepyihszqhnv:47e3570878ee79c79736372dd6876265ddc82a85bb00f804ad803ad339441bab@ec2-3-216-129-140.compute-1.amazonaws.com:5432/ddvccbrmvire6q"
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f= open("books.csv")
    freader = csv.reader(f)
    for isbn,title,author,year in freader:
        db.execute("INSERT INTO books (isbn, title, author,year) VALUES (:isbn, :title, :author, :year)",{"isbn":isbn,"title":title,"author":author,"year":year})
        print(f"added {isbn}")
    db.commit()

if __name__ == "__main__" :
    main()
