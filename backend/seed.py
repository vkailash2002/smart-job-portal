from database import Base, engine, SessionLocal
from models import User, Company, Job, Application, Skill

Base.metadata.create_all(bind=engine)

db = SessionLocal()

db.query(Application).delete()
db.query(Job).delete()
db.query(Company).delete()
db.query(User).delete()
db.query(Skill).delete()
db.commit()

users = [
    User(name="Arun Kumar", email="arun@gmail.com", password="pass123", role="job_seeker"),
    User(name="Priya Sharma", email="priya@gmail.com", password="pass123", role="job_seeker"),
    User(name="TechCorp HR", email="hr@techcorp.com", password="pass123", role="employer"),
    User(name="Innovate Ltd HR", email="hr@innovate.com", password="pass123", role="employer"),
]

db.add_all(users)
db.commit()

companies = [
    Company(company_name="TechCorp", location="Bangalore", description="Software Development Company", employer_id=3),
    Company(company_name="Innovate Ltd", location="Hyderabad", description="AI and Data Science Company", employer_id=4),
]

db.add_all(companies)
db.commit()

skills = [
    Skill(skill_name="JavaScript"),
    Skill(skill_name="React"),
    Skill(skill_name="FastAPI"),
    Skill(skill_name="Python"),
    Skill(skill_name="SQL"),
    Skill(skill_name="Machine Learning"),
    Skill(skill_name="Data Analysis"),
    Skill(skill_name="Node.js"),
]

db.add_all(skills)
db.commit()

skill_map = {skill.skill_name: skill for skill in db.query(Skill).all()}

jobs = [
    Job(
        title="Frontend Developer",
        description="Looking for a React developer.",
        location="Bangalore",
        salary=600000,
        company_id=1,
        skills=[skill_map["JavaScript"], skill_map["React"]],
    ),
    Job(
        title="Backend Developer",
        description="Looking for FastAPI and SQL developer.",
        location="Bangalore",
        salary=700000,
        company_id=1,
        skills=[skill_map["FastAPI"], skill_map["Python"], skill_map["SQL"]],
    ),
    Job(
        title="Data Analyst",
        description="SQL and Python required for data analysis.",
        location="Hyderabad",
        salary=650000,
        company_id=2,
        skills=[skill_map["SQL"], skill_map["Python"], skill_map["Data Analysis"]],
    ),
    Job(
        title="AI Engineer",
        description="Machine Learning experience required.",
        location="Hyderabad",
        salary=900000,
        company_id=2,
        skills=[skill_map["Python"], skill_map["Machine Learning"], skill_map["SQL"]],
    ),
]

db.add_all(jobs)
db.commit()

arun = db.query(User).filter(User.user_id == 1).first()
priya = db.query(User).filter(User.user_id == 2).first()

arun.skills = [skill_map["JavaScript"], skill_map["React"], skill_map["SQL"]]
priya.skills = [skill_map["Python"], skill_map["SQL"], skill_map["Machine Learning"]]

db.commit()

applications = [
    Application(user_id=1, job_id=1, status="applied"),
    Application(user_id=1, job_id=2, status="shortlisted"),
    Application(user_id=2, job_id=3, status="applied"),
    Application(user_id=2, job_id=4, status="rejected"),
]

db.add_all(applications)
db.commit()
db.close()

print("Database seeded successfully.")