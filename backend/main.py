from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from database import Base, engine, get_db
import models
import schemas

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Smart Job Portal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Smart Job Portal API is running"}


def get_or_create_skill(db: Session, skill_name: str):
    clean_name = skill_name.strip()

    skill = db.query(models.Skill).filter(
        models.Skill.skill_name.ilike(clean_name)
    ).first()

    if skill:
        return skill

    skill = models.Skill(skill_name=clean_name)
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@app.post("/users", response_model=schemas.UserOut)
def create_user(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        models.User.email == payload.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    if payload.role not in ["job_seeker", "employer"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = models.User(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.get("/users", response_model=list[schemas.UserOut])
def get_users(db: Session = Depends(get_db)):
    return db.query(models.User).order_by(models.User.user_id).all()


@app.post("/companies", response_model=schemas.CompanyOut)
def create_company(payload: schemas.CompanyCreate, db: Session = Depends(get_db)):
    employer = db.query(models.User).filter(
        models.User.user_id == payload.employer_id,
        models.User.role == "employer"
    ).first()

    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")

    company = models.Company(
        company_name=payload.company_name,
        location=payload.location,
        description=payload.description,
        employer_id=payload.employer_id,
    )

    db.add(company)
    db.commit()
    db.refresh(company)

    return company


@app.get("/companies", response_model=list[schemas.CompanyOut])
def get_companies(db: Session = Depends(get_db)):
    return db.query(models.Company).order_by(models.Company.company_id).all()


@app.post("/jobs", response_model=schemas.JobOut)
def create_job(payload: schemas.JobCreate, db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(
        models.Company.company_id == payload.company_id
    ).first()

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    job = models.Job(
        title=payload.title,
        description=payload.description,
        location=payload.location,
        salary=payload.salary,
        company_id=payload.company_id,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    for skill_name in payload.required_skills:
        if skill_name.strip():
            skill = get_or_create_skill(db, skill_name)
            job.skills.append(skill)

    db.commit()
    db.refresh(job)

    return schemas.JobOut(
        job_id=job.job_id,
        title=job.title,
        description=job.description,
        location=job.location,
        salary=job.salary,
        company_id=job.company_id,
        company_name=company.company_name,
        required_skills=[skill.skill_name for skill in job.skills],
    )


@app.get("/jobs", response_model=list[schemas.JobOut])
def get_jobs(db: Session = Depends(get_db)):
    jobs = (
        db.query(models.Job)
        .options(joinedload(models.Job.company), joinedload(models.Job.skills))
        .order_by(models.Job.job_id)
        .all()
    )

    return [
        schemas.JobOut(
            job_id=job.job_id,
            title=job.title,
            description=job.description,
            location=job.location,
            salary=job.salary,
            company_id=job.company_id,
            company_name=job.company.company_name if job.company else None,
            required_skills=[skill.skill_name for skill in job.skills],
        )
        for job in jobs
    ]


@app.get("/skills", response_model=list[schemas.SkillOut])
def get_skills(db: Session = Depends(get_db)):
    return db.query(models.Skill).order_by(models.Skill.skill_name).all()


@app.post("/applications", response_model=schemas.ApplicationOut)
def create_application(payload: schemas.ApplicationCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.user_id == payload.user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    job = (
        db.query(models.Job)
        .options(joinedload(models.Job.company))
        .filter(models.Job.job_id == payload.job_id)
        .first()
    )

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    existing_application = db.query(models.Application).filter(
        models.Application.user_id == payload.user_id,
        models.Application.job_id == payload.job_id,
    ).first()

    if existing_application:
        raise HTTPException(status_code=400, detail="User already applied to this job")

    application = models.Application(
        user_id=payload.user_id,
        job_id=payload.job_id,
        status="applied",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return schemas.ApplicationOut(
        application_id=application.application_id,
        user_id=user.user_id,
        user_name=user.name,
        job_id=job.job_id,
        job_title=job.title,
        company_name=job.company.company_name if job.company else None,
        status=application.status,
    )


@app.get("/applications", response_model=list[schemas.ApplicationOut])
def get_applications(db: Session = Depends(get_db)):
    applications = (
        db.query(models.Application)
        .options(
            joinedload(models.Application.user),
            joinedload(models.Application.job).joinedload(models.Job.company),
        )
        .order_by(models.Application.application_id)
        .all()
    )

    return [
        schemas.ApplicationOut(
            application_id=app.application_id,
            user_id=app.user_id,
            user_name=app.user.name if app.user else None,
            job_id=app.job_id,
            job_title=app.job.title if app.job else None,
            company_name=app.job.company.company_name if app.job and app.job.company else None,
            status=app.status,
        )
        for app in applications
    ]


@app.put("/applications/{application_id}", response_model=schemas.ApplicationOut)
def update_application_status(
    application_id: int,
    payload: schemas.ApplicationUpdate,
    employer_id: int,
    db: Session = Depends(get_db)
):
    allowed_statuses = ["applied", "reviewing", "shortlisted", "rejected"]

    if payload.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Invalid application status")

    application = (
        db.query(models.Application)
        .options(
            joinedload(models.Application.user),
            joinedload(models.Application.job).joinedload(models.Job.company),
        )
        .filter(models.Application.application_id == application_id)
        .first()
    )

    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    if not application.job or not application.job.company:
        raise HTTPException(status_code=400, detail="Invalid application record")

    if application.job.company.employer_id != employer_id:
        raise HTTPException(
            status_code=403,
            detail="You can only manage applications for your own company"
        )

    application.status = payload.status
    db.commit()
    db.refresh(application)

    return schemas.ApplicationOut(
        application_id=application.application_id,
        user_id=application.user_id,
        user_name=application.user.name if application.user else None,
        job_id=application.job_id,
        job_title=application.job.title if application.job else None,
        company_name=application.job.company.company_name if application.job and application.job.company else None,
        status=application.status,
    )

@app.post("/user-skills")
def save_user_skills(payload: schemas.UserSkillsCreate, db: Session = Depends(get_db)):
    user = (
        db.query(models.User)
        .options(joinedload(models.User.skills))
        .filter(models.User.user_id == payload.user_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    skills = db.query(models.Skill).filter(
        models.Skill.skill_id.in_(payload.skill_ids)
    ).all()

    user.skills = skills
    db.commit()

    return {
        "message": "User skills updated successfully",
        "user_id": user.user_id,
        "skills": [skill.skill_name for skill in skills],
    }


@app.get("/skill-matches/{user_id}", response_model=list[schemas.SkillMatchOut])
def get_skill_matches(user_id: int, db: Session = Depends(get_db)):
    user = (
        db.query(models.User)
        .options(joinedload(models.User.skills))
        .filter(models.User.user_id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user_skill_names = {skill.skill_name for skill in user.skills}

    jobs = (
        db.query(models.Job)
        .options(joinedload(models.Job.skills), joinedload(models.Job.company))
        .all()
    )

    results = []

    for job in jobs:
        required_skills = {skill.skill_name for skill in job.skills}

        if not required_skills:
            match_percentage = 0
            matched = []
            missing = []
        else:
            matched = sorted(list(user_skill_names.intersection(required_skills)))
            missing = sorted(list(required_skills.difference(user_skill_names)))
            match_percentage = round((len(matched) / len(required_skills)) * 100)

        results.append(
            schemas.SkillMatchOut(
                job_id=job.job_id,
                title=job.title,
                company_name=job.company.company_name if job.company else "Unknown Company",
                location=job.location,
                matched_skills=matched,
                missing_skills=missing,
                match_percentage=match_percentage,
            )
        )

    results.sort(key=lambda item: item.match_percentage, reverse=True)

    return results


@app.post("/login", response_model=schemas.UserOut)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()

    if not user or user.password != payload.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return user


@app.get("/employers/{employer_id}/applications", response_model=list[schemas.ApplicationOut])
def get_employer_applications(employer_id: int, db: Session = Depends(get_db)):
    employer = db.query(models.User).filter(
        models.User.user_id == employer_id,
        models.User.role == "employer"
    ).first()

    if not employer:
        raise HTTPException(status_code=404, detail="Employer not found")

    applications = (
        db.query(models.Application)
        .join(models.Job, models.Application.job_id == models.Job.job_id)
        .join(models.Company, models.Job.company_id == models.Company.company_id)
        .options(
            joinedload(models.Application.user),
            joinedload(models.Application.job).joinedload(models.Job.company),
        )
        .filter(models.Company.employer_id == employer_id)
        .order_by(models.Application.application_id.desc())
        .all()
    )

    return [
        schemas.ApplicationOut(
            application_id=app.application_id,
            user_id=app.user_id,
            user_name=app.user.name if app.user else None,
            job_id=app.job_id,
            job_title=app.job.title if app.job else None,
            company_name=app.job.company.company_name if app.job and app.job.company else None,
            status=app.status,
        )
        for app in applications
    ]



@app.get("/employers/{employer_id}/companies", response_model=list[schemas.CompanyOut])
def get_employer_companies(employer_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.Company)
        .filter(models.Company.employer_id == employer_id)
        .order_by(models.Company.company_id)
        .all()
    )


@app.post("/register", response_model=schemas.UserOut)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(
        models.User.email == payload.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    if payload.role not in ["job_seeker", "employer"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = models.User(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    if payload.role == "employer":
        if not payload.company_name:
            raise HTTPException(
                status_code=400,
                detail="Company name is required for employer registration"
            )

        company = models.Company(
            company_name=payload.company_name,
            location=payload.company_location,
            description=payload.company_description,
            employer_id=user.user_id,
        )

        db.add(company)
        db.commit()

    return user