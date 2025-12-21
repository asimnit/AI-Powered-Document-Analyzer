"""
User Database Model

Defines the User table structure in PostgreSQL.
- SQLAlchemy ORM model
- Represents the 'users' table
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    User Model
    
    Attributes:
        id: Primary key
        email: Unique email address
        username: Unique username
        hashed_password: Bcrypt hashed password (never store plain passwords!)
        full_name: User's full name
        is_active: Account active status
        is_superuser: Admin privileges
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # Timestamps - automatically managed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        """String representation for debugging"""
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"
