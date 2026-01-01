from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "postgresql://postgres:turon41@localhost:5432/userdatabase"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# ---------------- TABLES ----------------
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    verification_code = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    code_created_at = Column(DateTime, nullable=True)
    is_admin = Column(Boolean, default=False)
    full_name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)

class Hotel(Base):
    __tablename__ = "hotels"
    hotel_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)

class Dorm(Base):
    __tablename__ = "dorms"
    dorm_id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    location = Column(String)

class Fulltime(Base):
    __tablename__ = "fulltime"
    job_id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String)
    company_name = Column(String)
    salary = Column(Integer)    

class PartTime(Base):
    __tablename__ = "parttime"
    job_id = Column(Integer, primary_key=True, index=True)
    job_title = Column(String)
    institution_name = Column(String)
    salary = Column(Integer)


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemSettings(Base):
    __tablename__ = "system_settings"
    id = Column(Integer, primary_key=True, index=True)
    global_logout_time = Column(DateTime, nullable=True)

Base.metadata.create_all(bind=engine)
