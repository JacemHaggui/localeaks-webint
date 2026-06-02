from fastapi import FastAPI, Query, HTTPException, Depends, status, Body, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from sqlalchemy import text
from db import engine

from queries import (
    fetch_apartments_by_address,
    get_apartment_details,
    get_landlord_details,
    add_apartment,
    add_landlord,
    search_landlord_by_name
)

import random
import os
import json
from dotenv import load_dotenv

import cloudinary
import cloudinary.uploader

from email_utils import send_verification_email

load_dotenv()

# ----------------------------
# Cloudinary configuration
# ----------------------------
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# ----------------------------
# JWT configuration
# ----------------------------
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ----------------------------
# Password hashing setup
# ----------------------------
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# OAuth2 token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# ----------------------------
# Load allowed French university domains
# ----------------------------
with open("france_domains.json", "r", encoding="utf-8") as f:
    ALLOWED_DOMAINS = set(json.load(f))


def is_university_email(email: str) -> bool:
    """
    Returns True if the email belongs to a known French academic domain.
    This is based on a precomputed list of university domains.
    """
    if "@" not in email:
        return False

    domain = email.split("@", 1)[1].lower().strip()

    # Direct match
    if domain in ALLOWED_DOMAINS:
        return True

    # Optional: support subdomains (e.g. mail.univ-paris1.fr)
    for allowed in ALLOWED_DOMAINS:
        if domain == allowed or domain.endswith("." + allowed):
            return True

    return False


# ----------------------------
# FastAPI app setup
# ----------------------------
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----------------------------
# Security helpers
# ----------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Creates a JWT access token for authentication.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Extracts user ID from JWT token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        return user_id

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ----------------------------
# Registration endpoint
# ----------------------------
@app.post("/register")
def signup(user: dict):
    name = user.get("name")
    email = user.get("email")
    password = user.get("password")

    if not all([name, email, password]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    # Enforce university email restriction
    if not is_university_email(email):
        raise HTTPException(status_code=400, detail="University email required")

    hashed_password = get_password_hash(password)

    with engine.begin() as conn:

        # Check if email already exists
        existing = conn.execute(
            text("SELECT id FROM student WHERE email = :email"),
            {"email": email}
        ).fetchone()

        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create student account
        result = conn.execute(
            text("""
                INSERT INTO student (name, email, password_hash, created_at, is_verified)
                VALUES (:name, :email, :password_hash, NOW(), FALSE)
                RETURNING id
            """),
            {"name": name, "email": email, "password_hash": hashed_password}
        )

        student_id = result.fetchone()[0]

        # Generate email verification code
        code = random.randint(100000, 999999)
        expires_at = datetime.now() + timedelta(minutes=15)

        conn.execute(
            text("""
                INSERT INTO student_verification (student_id, code, expires_at)
                VALUES (:student_id, :code, :expires_at)
            """),
            {"student_id": student_id, "code": code, "expires_at": expires_at}
        )

        send_verification_email(email, name, str(code))

    return {"status": "success"}


# ----------------------------
# Email verification endpoint
# ----------------------------
@app.post("/verify")
def verify_email(data: dict):
    email = data.get("email")
    code = data.get("code")

    if not email or not code:
        raise HTTPException(status_code=400)

    with engine.begin() as conn:

        row = conn.execute(
            text("""
                SELECT s.id, v.code, v.expires_at
                FROM student s
                JOIN student_verification v ON s.id = v.student_id
                WHERE s.email = :email
            """),
            {"email": email}
        ).fetchone()

        if not row:
            raise HTTPException(status_code=400)

        if datetime.now() > row.expires_at:
            raise HTTPException(status_code=400)

        if str(code) != str(row.code):
            raise HTTPException(status_code=400)

        conn.execute(
            text("UPDATE student SET is_verified = TRUE WHERE id = :student_id"),
            {"student_id": row.id}
        )

        conn.execute(
            text("DELETE FROM student_verification WHERE student_id = :student_id"),
            {"student_id": row.id}
        )

    return {"status": "success"}


# ----------------------------
# Login endpoint
# ----------------------------
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with engine.connect() as conn:

        user = conn.execute(
            text("SELECT id, password_hash, is_verified FROM student WHERE email = :email"),
            {"email": form_data.username}
        ).fetchone()

        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(status_code=401)

        if not user.is_verified:
            raise HTTPException(status_code=403)

        token = create_access_token({"sub": str(user.id)})
        return {"access_token": token, "token_type": "bearer"}


# ----------------------------
# Current user endpoint
# ----------------------------
@app.get("/me")
def read_current_user(user_id: int = Depends(get_current_user)):
    with engine.connect() as conn:

        user = conn.execute(
            text("SELECT id, name, email FROM student WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404)

        return {"id": user.id, "name": user.name, "email": user.email}


# ----------------------------
# Apartment endpoints
# ----------------------------
@app.get("/apartments")
def get_apartments(address: str = Query(...), user_id: int = Depends(get_current_user)):
    return {"apartments": fetch_apartments_by_address(address)}


@app.get("/apartment/{apartment_id}")
def apartment_details(apartment_id: int, user_id: int = Depends(get_current_user)):
    apartment = get_apartment_details(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404)
    return apartment


@app.post("/apartments")
def create_apartment(apartment: dict, user_id: int = Depends(get_current_user)):
    add_apartment(apartment)
    return {"status": "success"}


# ----------------------------
# File upload (Cloudinary)
# ----------------------------
@app.post("/apartment/{apartment_id}/photos")
async def upload_apartment_photo(
    apartment_id: int,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user)
):
    upload_result = cloudinary.uploader.upload(
        file.file,
        folder="apartments"
    )

    url = upload_result.get("secure_url")

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO apartment_photo (apartment_id, url)
                VALUES (:apartment_id, :url)
            """),
            {"apartment_id": apartment_id, "url": url}
        )

    return {"url": url}


# ----------------------------
# Reviews
# ----------------------------
@app.post("/reviews")
def add_review(review: dict, user_id: int = Depends(get_current_user)):

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO apartment_review
                (apartment_id, student_id, cleanliness, value_for_money, amenities, overall, comment, created_at)
                VALUES
                (:apartment_id, :student_id, :cleanliness, :value_for_money, :amenities, :overall, :comment, NOW())
            """),
            {**review, "student_id": user_id}
        )

    return {"status": "success"}


@app.post("/landlord-reviews")
def add_landlord_review(review: dict, user_id: int = Depends(get_current_user)):

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO landlord_review
                (landlord_id, student_id, responsiveness, maintenance, communication, fairness, overall, comment, created_at)
                VALUES
                (:landlord_id, :student_id, :responsiveness, :maintenance, :communication, :fairness, :overall, :comment, NOW())
            """),
            {**review, "student_id": user_id}
        )

    return {"status": "success"}


# ----------------------------
# Landlord endpoints
# ----------------------------
@app.get("/landlord/{landlord_id}")
def landlord_details(landlord_id: int, user_id: int = Depends(get_current_user)):
    data = get_landlord_details(landlord_id)

    if not data:
        raise HTTPException(status_code=404, detail="Landlord not found")

    return data


@app.post("/landlords")
def create_landlord(landlord: dict, user_id: int = Depends(get_current_user)):
    return add_landlord(landlord)


@app.get("/landlords")
def search_landlords(search: str, user_id: int = Depends(get_current_user)):
    return search_landlord_by_name(search)


@app.delete("/me")
def delete_account(
    password: str = Body(..., embed=True),
    deleteReviews: bool = Body(False, embed=True),
    user_id: int = Depends(get_current_user)
):
    with engine.begin() as conn:

        user = conn.execute(
            text("SELECT password_hash FROM student WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not user:
            raise HTTPException(status_code=404)

        if not pwd_context.verify(password, user.password_hash):
            raise HTTPException(status_code=401)

        # ----------------------------
        # Case 1: full wipe
        # ----------------------------
        if deleteReviews:
            conn.execute(
                text("DELETE FROM apartment_review WHERE student_id = :id"),
                {"id": user_id}
            )
            conn.execute(
                text("DELETE FROM landlord_review WHERE student_id = :id"),
                {"id": user_id}
            )
            conn.execute(
                text("DELETE FROM student WHERE id = :id"),
                {"id": user_id}
            )

        # ----------------------------
        # Case 2: keep reviews, anonymize user
        # ----------------------------
        else:
            conn.execute(text("""
                UPDATE student
                SET name = 'Ex-LocaLeaker',
                    email = 'deleted_' || id || '@local.invalid',
                    password_hash = '$disabled$',
                WHERE id = :id
            """), {"id": user_id})

    return {"status": "success"}