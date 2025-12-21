"""
Authentication Endpoints

Handles user registration, login, and authentication.
- POST /register - Create new user account
- POST /login - Authenticate and get JWT token
- GET /me - Get current user info (requires auth)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token, UserLogin

logger = get_logger(__name__)

router = APIRouter()

# OAuth2 scheme for token authentication
# tokenUrl is where frontend sends login credentials
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user
    
    - Extracts JWT token from Authorization header
    - Verifies token and gets user ID
    - Fetches user from database
    - Returns user or raises 401 error
    
    Usage in routes:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"user": current_user.email}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token and get user ID
    user_id = verify_token(token)
    if user_id is None:
        logger.warning("Invalid or expired token provided")
        raise credentials_exception
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        logger.warning(f"Token valid but user_id={user_id} not found in database")
        raise credentials_exception
    
    logger.debug(f"User authenticated: {user.username} (id={user.id})")
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    
    Steps:
    1. Check if email/username already exists
    2. Hash the password
    3. Create user in database
    4. Return user data (without password!)
    """
    
    logger.info(f"Registration attempt: username={user_data.username}, email={user_data.email}")
    
    # Check if email already exists
    if db.query(User).filter(User.email == user_data.email).first():
        logger.warning(f"Registration failed: email {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if db.query(User).filter(User.username == user_data.username).first():
        logger.warning(f"Registration failed: username {user_data.username} already taken")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"✅ User registered successfully: {db_user.username} (id={db_user.id})")
    return db_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get JWT token
    
    Steps:
    1. Find user by username
    2. Verify password
    3. Create JWT token
    4. Return token
    
    Frontend will store this token and send it with every request
    """
    
    logger.info(f"Login attempt: username={form_data.username}")
    
    # Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()
    
    # Check if user exists and password is correct
    if not user or not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"❌ Login failed: incorrect credentials for username={form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"❌ Login failed: inactive user {user.username} (id={user.id})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token and refresh token
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    logger.info(f"✅ Login successful: {user.username} (id={user.id})")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user
    
    This is a protected route - requires valid JWT token.
    Frontend can call this to get user info after login.
    """
    logger.debug(f"User profile requested: {current_user.username} (id={current_user.id})")
    return current_user


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    Steps:
    1. Verify refresh token
    2. Get user from database
    3. Generate new access token and refresh token
    4. Return new tokens
    
    This allows users to stay logged in without re-entering credentials
    """
    logger.info("Token refresh attempt")
    
    # Verify refresh token
    user_id = verify_token(refresh_token, token_type="refresh")
    
    if user_id is None:
        logger.warning("❌ Token refresh failed: invalid refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = db.query(User).filter(User.id == int(user_id)).first()
    
    if not user:
        logger.warning(f"❌ Token refresh failed: user_id={user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Check if user is still active
    if not user.is_active:
        logger.warning(f"❌ Token refresh failed: inactive user {user.username} (id={user.id})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    logger.info(f"✅ Token refresh successful: {user.username} (id={user.id})")
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }
