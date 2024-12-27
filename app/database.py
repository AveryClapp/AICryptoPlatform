from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql
import os
from dotenv import load_dotenv

load_dotenv()
db_pass = os.environ.get("DB_PASS")
connection = pymysql.connect(
    user='root',
    host='127.0.0.1',
    port=3306,
    password=db_pass,
    database='crypto-pltf',
    cursorclass=pymysql.cursors.DictCursor
)

engine = create_engine('mysql+pymysql://', creator=lambda: connection)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

