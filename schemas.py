from pydantic import BaseModel, EmailStr,ConfigDict
from typing import Optional
from enum import Enum


class AccommodationName(str, Enum):
    hotel = "hotel"
    dorm = "dorm"


class UserCreate(BaseModel):
    email: EmailStr
    password: str

class VerifyCode(BaseModel):
    email: EmailStr
    code: str

class UserUpdate(BaseModel):
    full_name: Optional[str]
    age: Optional[int]

class HotelCreate(BaseModel):
    name: str
    location: str

class DormCreate(BaseModel):
    name: str
    location: str
    
class Fulltime(BaseModel):
    job_id: int
    job_title: str
    company_name: str
    salary: int   

class PartTime(BaseModel):
    job_id: int
    job_title: str
    institution_name: str
    salary: int
    

    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    full_name: str | None = None
    age: int | None = None

class AccommodationName(str,Enum):
    permanent = "permanent"
    temporary = "temporary"


class JobType(str,Enum):
    fullTime = "full-time"
    partTime = "part-time"    