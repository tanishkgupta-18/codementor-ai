from argon2 import PasswordHasher
from jose import jwt
from datetime import datetime, timedelta, timezone
from fastapi import Header, HTTPException
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

ph = PasswordHasher()


def hash_password(password: str):
    return ph.hash(password)


def verify_password(plain, hashed):
    try:
        ph.verify(hashed, plain)
        return True
    except:
        return False


def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: str = Header(...)):
    try:
        token = authorization.split(" ")[1]
        data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return data["email"]
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
