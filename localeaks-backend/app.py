# app.py
from fastapi import FastAPI, Query, HTTPException, Depends, status
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

# email sending
from email_utils import send_verification_email

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
from dotenv import load_dotenv
load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Use Argon2 instead of bcrypt
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ---------------------------
# Utility functions
# ---------------------------
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ---------------------------
# Register (create student + verification code)
# ---------------------------
@app.post("/register")
def signup(user: dict):
    name = user.get("name")
    email = user.get("email")
    password = user.get("password")

    if not all([name, email, password]):
        raise HTTPException(status_code=400, detail="Missing required fields")

    hashed_password = get_password_hash(password)

    with engine.begin() as conn:
        # check if email exists
        existing = conn.execute(text("SELECT id FROM student WHERE email = :email"), {"email": email}).fetchone()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # insert student
        result = conn.execute(
            text("INSERT INTO student (name, email, password_hash, created_at, is_verified) "
                 "VALUES (:name, :email, :password_hash, NOW(), FALSE) RETURNING id"),
            {"name": name, "email": email, "password_hash": hashed_password}
        )
        student_id = result.fetchone()[0]

        # generate verification code
        code = random.randint(100000, 999999)
        expires_at = datetime.now() + timedelta(minutes=15)
        conn.execute(
            text("INSERT INTO student_verification (student_id, code, expires_at) "
                 "VALUES (:student_id, :code, :expires_at)"),
            {"student_id": student_id, "code": code, "expires_at": expires_at}
        )
        # send code by email using Mailgun
        status, msg = send_verification_email(email, name, str(code))
        print(f"[MAILGUN] Email sent to {email} — status {status}: {msg}")

    return {"status": "success", "message": "User created. Verification code sent via email."}


# ---------------------------
# Verify email
# ---------------------------
@app.post("/verify")
def verify_email(data: dict):
    email = data.get("email")
    code = data.get("code")

    if not email or not code:
        raise HTTPException(status_code=400, detail="Email and code are required")

    with engine.begin() as conn:
        row = conn.execute(
            text("SELECT s.id, v.code, v.expires_at FROM student s "
                 "JOIN student_verification v ON s.id = v.student_id "
                 "WHERE s.email = :email"),
            {"email": email}
        ).fetchone()

        if not row:
            raise HTTPException(status_code=400, detail="No verification found for this email")

        if datetime.now() > row.expires_at:
            raise HTTPException(status_code=400, detail="Verification code expired")

        if str(code) != str(row.code):
            raise HTTPException(status_code=400, detail="Invalid verification code")

        # mark student as verified
        conn.execute(
            text("UPDATE student SET is_verified = TRUE WHERE id = :student_id"),
            {"student_id": row.id}
        )

        # optional: delete verification code
        conn.execute(
            text("DELETE FROM student_verification WHERE student_id = :student_id"),
            {"student_id": row.id}
        )

    return {"status": "success", "message": "Email verified successfully"}


# ---------------------------
# Login (only verified users)
# ---------------------------
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT id, password_hash, is_verified FROM student WHERE email = :email"),
            {"email": form_data.username}
        ).fetchone()

        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Incorrect email or password")

        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Email not verified")

        token = create_access_token({"sub": str(user.id)})
        return {"access_token": token, "token_type": "bearer"}


# ---------------------------
# Current user info
# ---------------------------
@app.get("/me")
def read_current_user(user_id: int = Depends(get_current_user)):
    with engine.connect() as conn:
        user = conn.execute(
            text("SELECT id, name, email FROM student WHERE id = :id"),
            {"id": user_id}
        ).fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.id, "name": user.name, "email": user.email}


# ---------------------------
# Restricted apartment & landlord routes
# ---------------------------
@app.get("/apartments")
def get_apartments(address: str = Query(...), user_id: int = Depends(get_current_user)):
    apartments = fetch_apartments_by_address(address)
    return {"apartments": apartments}


@app.get("/apartment/{apartment_id}")
def apartment_details(apartment_id: int, user_id: int = Depends(get_current_user)):
    apartment = get_apartment_details(apartment_id)
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")
    return apartment


@app.get("/landlord/{landlord_id}")
def landlord_details(landlord_id: int, user_id: int = Depends(get_current_user)):
    landlord = get_landlord_details(landlord_id)
    if not landlord:
        raise HTTPException(status_code=404, detail="Landlord not found")
    return landlord


@app.post("/apartments")
def create_apartment(apartment: dict, user_id: int = Depends(get_current_user)):
    try:
        add_apartment(apartment)
        return {"status": "success", "message": "Appartement ajouté avec succès"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# ---------------------------
# Add apartment review
# ---------------------------
@app.post("/reviews")
def add_review(review: dict, user_id: int = Depends(get_current_user)):
    """
    Expects JSON body:
    {
        "apartment_id": int,
        "cleanliness": int,
        "value_for_money": int,
        "amenities": int,
        "overall": int,
        "comment": str (optional)
    }
    """
    apartment_id = review.get("apartment_id")
    cleanliness = review.get("cleanliness")
    value_for_money = review.get("value_for_money")
    amenities = review.get("amenities")
    overall = review.get("overall")
    comment = review.get("comment", "")

    if not all([apartment_id, cleanliness is not None, value_for_money is not None, amenities is not None, overall is not None]):
        raise HTTPException(status_code=400, detail="Missing required review fields")

    # Validate integers 0-10
    for score in [cleanliness, value_for_money, amenities, overall]:
        if not isinstance(score, int) or score < 0 or score > 10:
            raise HTTPException(status_code=400, detail="Scores must be integers between 0 and 10")

    with engine.begin() as conn:
        # Check that apartment exists
        apartment = conn.execute(text("SELECT id FROM apartment WHERE id = :id"), {"id": apartment_id}).fetchone()
        if not apartment:
            raise HTTPException(status_code=404, detail="Apartment not found")

        # Insert review
        conn.execute(
            text(
                "INSERT INTO apartment_review "
                "(apartment_id, student_id, cleanliness, value_for_money, amenities, overall, comment, created_at) "
                "VALUES (:apartment_id, :student_id, :cleanliness, :value_for_money, :amenities, :overall, :comment, NOW())"
            ),
            {
                "apartment_id": apartment_id,
                "student_id": user_id,
                "cleanliness": cleanliness,
                "value_for_money": value_for_money,
                "amenities": amenities,
                "overall": overall,
                "comment": comment
            }
        )

    return {"status": "success", "message": "Avis ajouté avec succès"}

@app.post("/landlord-reviews")
def add_landlord_review(review: dict, user_id: int = Depends(get_current_user)):
    """
    Expects JSON body:
    {
        "landlord_id": int,
        "responsiveness": int,
        "maintenance": int,
        "communication": int,
        "fairness": int,
        "overall": int,
        "comment": str (optional)
    }
    """
    landlord_id = review.get("landlord_id")
    responsiveness = review.get("responsiveness")
    maintenance = review.get("maintenance")
    communication = review.get("communication")
    fairness = review.get("fairness")
    overall = review.get("overall")
    comment = review.get("comment", "")

    if not all([
        landlord_id,
        responsiveness is not None,
        maintenance is not None,
        communication is not None,
        fairness is not None,
        overall is not None
    ]):
        raise HTTPException(status_code=400, detail="Missing required review fields")

    # Validate that all scores are integers between 0 and 10
    for score in [responsiveness, maintenance, communication, fairness, overall]:
        if not isinstance(score, int) or score < 0 or score > 10:
            raise HTTPException(status_code=400, detail="Scores must be integers between 0 and 10")

    with engine.begin() as conn:
        # Check that landlord exists
        landlord = conn.execute(
            text("SELECT id FROM landlord WHERE id = :id"),
            {"id": landlord_id}
        ).fetchone()
        if not landlord:
            raise HTTPException(status_code=404, detail="Landlord not found")

        # Insert review
        conn.execute(
            text("""
                INSERT INTO landlord_review (
                    landlord_id, student_id,
                    responsiveness, maintenance, communication, fairness, overall, comment, created_at
                ) VALUES (
                    :landlord_id, :student_id,
                    :responsiveness, :maintenance, :communication, :fairness, :overall, :comment, NOW()
                )
            """),
            {
                "landlord_id": landlord_id,
                "student_id": user_id,
                "responsiveness": responsiveness,
                "maintenance": maintenance,
                "communication": communication,
                "fairness": fairness,
                "overall": overall,
                "comment": comment
            }
        )

    return {"status": "success", "message": "Avis ajouté avec succès"}


@app.post("/landlords")
def create_landlord(landlord: dict, user_id: int = Depends(get_current_user)):
    try:
        new_landlord = add_landlord(landlord)
        return new_landlord
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/landlords")
def search_landlords(search: str, user_id: int = Depends(get_current_user)):
    return search_landlord_by_name(search)


from fastapi import Body

@app.delete("/me")
def delete_account(
    password: str = Body(..., embed=True),
    deleteReviews: bool = Body(False, embed=True),
    user_id: int = Depends(get_current_user)
):
    with engine.begin() as conn:
        # Fetch user's current password hash
        user = conn.execute(
            text("SELECT password_hash FROM student WHERE id = :id"),
            {"id": user_id}
        ).fetchone()

        if not user or not pwd_context.verify(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Password incorrect")

        if deleteReviews:
            # Delete all apartment reviews
            conn.execute(
                text("DELETE FROM apartment_review WHERE student_id = :id"),
                {"id": user_id}
            )
            # Delete all landlord reviews by this student
            conn.execute(
                text("DELETE FROM landlord_review WHERE student_id = :id"),
                {"id": user_id}
            )
        else:
            # Keep reviews but replace name with Ex-LocaLeaker
            placeholder_email = f"exlocaleaker+{user_id}@deleted.local"
            conn.execute(
                text("UPDATE student SET name = 'Ex-LocaLeaker', email = :email WHERE id = :id"),
                {"id": user_id, "email": placeholder_email}
            )

    return {"status": "success", "message": "Account deleted successfully"}