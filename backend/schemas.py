from pydantic import BaseModel, EmailStr
from typing import Optional, List
from decimal import Decimal


class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str


class UserOut(BaseModel):
    user_id: int
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True


class CompanyCreate(BaseModel):
    company_name: str
    location: Optional[str] = None
    description: Optional[str] = None
    employer_id: int


class CompanyOut(BaseModel):
    company_id: int
    company_name: str
    location: Optional[str]
    description: Optional[str]
    employer_id: Optional[int]

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    title: str
    description: str
    location: Optional[str] = None
    salary: Optional[Decimal] = None
    company_id: int
    required_skills: List[str] = []


class JobOut(BaseModel):
    job_id: int
    title: str
    description: str
    location: Optional[str]
    salary: Optional[Decimal]
    company_id: Optional[int]
    company_name: Optional[str] = None
    required_skills: List[str] = []

    class Config:
        from_attributes = True


class ApplicationCreate(BaseModel):
    user_id: int
    job_id: int


class ApplicationUpdate(BaseModel):
    status: str


class ApplicationOut(BaseModel):
    application_id: int
    user_id: int
    user_name: Optional[str] = None
    job_id: int
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    status: str

    class Config:
        from_attributes = True


class SkillOut(BaseModel):
    skill_id: int
    skill_name: str

    class Config:
        from_attributes = True


class UserSkillsCreate(BaseModel):
    user_id: int
    skill_ids: List[int]


class SkillMatchOut(BaseModel):
    job_id: int
    title: str
    company_name: str
    location: Optional[str]
    matched_skills: List[str]
    missing_skills: List[str]
    match_percentage: int


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str
    company_name: Optional[str] = None
    company_location: Optional[str] = None
    company_description: Optional[str] = None