from fastapi import FastAPI, Depends, HTTPException, status
from fastapi_pagination import Page, add_pagination,paginate      # type: ignore

from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
import crud, schemas
from database import SessionLocal
from jose import JWTError, jwt
from datetime import datetime
from schemas import AccommodationName, Fulltime,JobType,PartTime,HotelCreate,DormCreate
from sqlalchemy.orm import Session
import crud
from database import SessionLocal
from database import SystemSettings



app = FastAPI(title="Easy_Abroad")
add_pagination(app)


# ---------------- CONFIG ----------------
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")
SECRET_KEY = crud.SECRET_KEY
ALGORITHM = crud.ALGORITHM


# ---------------- DATABASE DEPENDENCY ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------- AUTH HELPER ----------------
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # check if blacklisted
        if db.query(crud.BlacklistedToken).filter(crud.BlacklistedToken.token == token).first():
            raise HTTPException(status_code=401, detail="Token blacklisted")

        user = crud.get_user(db, email)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# ---------------- SIGNUP / VERIFY ----------------
@app.post("/signup")
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        if db.query(crud.User).filter(crud.User.email == user.email).first():
            raise HTTPException(status_code=400, detail="User already exists")
        new_user = crud.create_user(db, user.email, user.password)
        return {"message": "Sign up successful", "verification_code": new_user.verification_code}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/verify")
def verify(code: schemas.VerifyCode, db: Session = Depends(get_db)):
    result = crud.verify_user(db, code.email, code.code)
    if result != "Verified":
        raise HTTPException(status_code=400, detail=result)
    return {"message": "You are verified"}


# ---------------- LOGIN / LOGOUT ----------------
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = crud.get_user(db, form_data.username)
    if not user or not user.is_verified:
        raise HTTPException(status_code=401, detail="Invalid credentials or not verified")
    if not crud.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = crud.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/logout")
def logout(current_user=Depends(get_current_user), token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    crud.blacklist_token(db, token)
    return {"message": "Logged out successfully"}



# ------------------ all log out -----------------


@app.post("/admin/logout-all")
def logout_all(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    settings = db.query(SystemSettings).first()   # 👈 use SystemSettings, not crud.SystemSettings
    if not settings:
        settings = SystemSettings()
        db.add(settings)

    settings.global_logout_time = datetime.utcnow()
    db.commit()
    return {"message": "All users have been logged out"}




# ---------------- PROFILE (User Protected Routes) ----------------
@app.put("/profile/update")
def update_profile(
    data: schemas.UserUpdate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update profile info for logged-in user."""
    updated_user = crud.update_user(db, current_user.email, data.dict())
    if not updated_user:
        raise HTTPException(status_code=400, detail="User not found or not verified")
    return {
        "message": "Profile updated successfully",
        "email": updated_user.email,
        "full_name": updated_user.full_name,
        "age": updated_user.age
    }






# ----------------------- see me --------------------
@app.get("/profile/me")
def get_my_profile(current_user=Depends(get_current_user)):
    """
    Get the currently logged-in user's full details.
    Requires a valid Bearer token.
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "age": current_user.age,
        "is_verified": current_user.is_verified,
        "is_admin": current_user.is_admin,
        "created_at": str(current_user.code_created_at) if current_user.code_created_at else None
    }


# ---------------- ADMIN ROUTES ----------------
@app.post("/admin/add-hotel")
def add_hotel(hotel: schemas.HotelCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    new_hotel = crud.add_hotel(db, hotel.dict())
    return {"hotel_id": new_hotel.hotel_id, "message": "Hotel added"}


@app.post("/admin/add-dorm")
def add_dorm(dorm: schemas.DormCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    new_dorm = crud.add_dorm(db, dorm.model_dump())
    return {"dorm_id": new_dorm.dorm_id, "message": "Dorm added"}




#----------------------------Dorms & Hotels-----------------------------

@app.get("/hotels",response_model=Page[HotelCreate]) # Only admin access
def list_hotels(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    items = crud.get_hotels(db)
    return paginate(items)


@app.get("/dorms",response_model=Page[DormCreate])   # Only admin access
def list_dorms(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return paginate(crud.get_dorms(db))



#----------------------------Fulltime & Parttime-----------------------------


@app.get("/fulltimejob",response_model=Page[Fulltime])  # Only admin access
def fulltime_jobs(
    current_user=Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    items = crud.get_fulltime(db)
    return paginate(items)



@app.get("/parttimejob", response_model=Page[PartTime])           # Only admin access
def parttime_jobs(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    items = crud.get_parttime(db)   # should return a SQLAlchemy query
    return paginate(items)







# -------------------------- Accommodation --------------------------
@app.get("/accommodation/{accommodation_name}")
def get_accommodation(
    accommodation_name: AccommodationName,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="User not verified")

    if accommodation_name == AccommodationName.temporary:
        hotels = crud.get_hotels(db)
        return {
            "type": "temporary",
            "message": "Here are some hotel suggestions for temporary accommodation",
            "options": hotels
        }

    elif accommodation_name == AccommodationName.permanent:
        dorms = crud.get_dorms(db)
        return {
            "type": "permanent",
            "message": "Here are some dormitory suggestions for permanent accommodation",
            "options": dorms
        }

    raise HTTPException(status_code=404, detail="Accommodation type not found")




# --------------------------JobType --------------------------


@app.get("/job/{job_type}")
def get_job(
    job_type: JobType,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    

    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="User not verified")

    if job_type == JobType.fullTime:
        items = crud.get_fulltime(db)
        return {
            "type": "full-time",
            "message": "Here are some full-time job suggestions",
            "options": items
        }    
    
    elif job_type == JobType.partTime:
        parttime = crud.get_parttime(db)
        return {
            "type": "part-time",
            "message": "Here are some part-time job suggestions for students",
            "options": parttime
        }


    raise HTTPException(status_code=404, detail="Job type not found")