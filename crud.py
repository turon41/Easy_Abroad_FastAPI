from sqlalchemy.orm import Session
from database import User, Hotel, Dorm, BlacklistedToken,Fulltime,PartTime
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import random, string

# ---------------- Security ----------------
SECRET_KEY = "supersecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password[:72])  # bcrypt limit

def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def generate_verification_code(length=6):
    return "".join(random.choices(string.digits, k=length))

# ---------------- User ----------------
def create_user(db: Session, email: str, password: str):
    hashed_pw = hash_password(password)
    code = generate_verification_code()
    user = User(email=email, password=hashed_pw, verification_code=code,
                is_verified=False, code_created_at=datetime.utcnow())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def verify_user(db: Session, email: str, code: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return "User not found"
    if user.verification_code != code:
        return "Invalid code"
    user.is_verified = True
    user.verification_code = None
    db.commit()
    return "Verified"

def get_user(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

# ---------------- Hotels / Dorms ----------------
def add_hotel(db: Session, data: dict):
    hotel = Hotel(**data)
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel

def add_dorm(db: Session, data: dict):
    dorm = Dorm(**data)
    db.add(dorm)
    db.commit()
    db.refresh(dorm)
    return dorm

def get_hotels(db: Session):
    return db.query(Hotel).all()

def get_dorms(db: Session):
    return db.query(Dorm).all()


# ---------------- Fulltime/ Parttime job ----------------


def get_fulltime(db: Session):
    return db.query(Fulltime).all()


def get_parttime(db:Session):
    return db.query(PartTime).all()


# ---------------- Logout ----------------
def blacklist_token(db: Session, token: str):
    blk = BlacklistedToken(token=token)
    db.add(blk)
    db.commit()

def update_user(db: Session, email: str, data: dict):
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_verified:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user

