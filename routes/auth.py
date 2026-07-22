import hashlib
import hmac
import secrets
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user_profile import UserProfile
from schemas import SignUpRequest, SignInRequest, ChangePasswordRequest, AuthResponse
from utils import logger

router = APIRouter()

def hash_password(password: str, salt_hex: str = None) -> tuple[str, str]:
    """
    Hashes password using scrypt with a unique 16-byte salt per user.
    Returns (hash_hex, salt_hex).
    """
    if not salt_hex:
        salt_bytes = secrets.token_bytes(16)
        salt_hex = salt_bytes.hex()
    else:
        salt_bytes = bytes.fromhex(salt_hex)
        
    key = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt_bytes,
        n=16384,
        r=8,
        p=1,
        dklen=32
    )
    return key.hex(), salt_hex

def verify_password(password: str, stored_hash_hex: str, stored_salt_hex: str) -> bool:
    """
    Verifies a raw password against stored scrypt hash and salt in constant time.
    """
    if not stored_hash_hex or not stored_salt_hex:
        return False
    computed_hash_hex, _ = hash_password(password, stored_salt_hex)
    return hmac.compare_digest(computed_hash_hex, stored_hash_hex)

@router.post("/signup", response_model=AuthResponse)
def sign_up(request: SignUpRequest, db: Session = Depends(get_db)):
    email_clean = request.email.strip().lower()
    if not email_clean:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required."
        )

    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )

    # Check if account already exists with this email
    existing_user = db.query(UserProfile).filter(UserProfile.email == email_clean).first()
    if existing_user:
        logger.info(f"Sign up failed: email {email_clean} already registered.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please sign in instead."
        )

    # Hash password with a fresh random salt
    pwd_hash, pwd_salt = hash_password(request.password)
    sync_token = request.sync_token or str(uuid.uuid4())

    new_user = UserProfile(
        name=request.name.strip(),
        email=email_clean,
        password_hash=pwd_hash,
        password_salt=pwd_salt,
        sync_token=sync_token,
        ai_enabled=request.ai_enabled or False,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"User signed up successfully: {email_clean}")

    return AuthResponse(
        status="success",
        sync_token=new_user.sync_token,
        name=new_user.name,
        email=new_user.email,
        ai_enabled=new_user.ai_enabled,
    )

@router.post("/signin", response_model=AuthResponse)
def sign_in(request: SignInRequest, db: Session = Depends(get_db)):
    email_clean = request.email.strip().lower()
    if not email_clean or not request.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and password are required."
        )

    user = db.query(UserProfile).filter(UserProfile.email == email_clean).first()
    if not user or not user.password_hash or not user.password_salt:
        logger.info(f"Sign in attempt failed for email: {email_clean}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not verify_password(request.password, user.password_hash, user.password_salt):
        logger.info(f"Sign in attempt failed (invalid password) for email: {email_clean}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    logger.info(f"User signed in successfully: {email_clean}")

    return AuthResponse(
        status="success",
        sync_token=user.sync_token,
        name=user.name,
        email=user.email,
        ai_enabled=user.ai_enabled or False,
    )

@router.post("/change-password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):
    email_clean = request.email.strip().lower()
    if not email_clean or not request.current_password or not request.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email, current password, and new password are required."
        )

    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long."
        )

    user = db.query(UserProfile).filter(UserProfile.email == email_clean).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found."
        )

    if not user.password_hash or not user.password_salt:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password configured for this user account."
        )

    if not verify_password(request.current_password, user.password_hash, user.password_salt):
        logger.info(f"Password change failed (incorrect current password) for email: {email_clean}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect current password."
        )

    new_hash, new_salt = hash_password(request.new_password)
    user.password_hash = new_hash
    user.password_salt = new_salt

    db.commit()
    logger.info(f"Password updated successfully for email: {email_clean}")

    return {"status": "success", "message": "Password updated successfully."}

