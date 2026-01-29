from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, text
from sqlalchemy.orm import relationship, declarative_base
import uuid
import datetime

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Profile(Base):
    __tablename__ = "profiles"

    # SQLite: Use String for UUIDs
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True)
    pabbly_customer_id = Column(String, unique=True, index=True, nullable=True)
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="user")
    api_keys = relationship("ApiKey", back_populates="user")

class ApiKey(Base):
    __tablename__ = "api_keys"

    key = Column(String, primary_key=True)  # e.g. sk_live_...
    user_id = Column(String, ForeignKey("profiles.id"))
    status = Column(String, default="active") # active, revoked
    
    # SQLite doesn't have server_default=text("now()") equivalent that works perfectly across versions
    # easier to handle in Python
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("Profile", back_populates="api_keys")

class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String, primary_key=True) # Pabbly Subscription ID
    user_id = Column(String, ForeignKey("profiles.id"))
    plan_code = Column(String, nullable=False)
    status = Column(String, nullable=False)    
    
    # SQLite stores DateTimes as Strings implicitly, SQLAlchemy handles the conversion
    current_period_end = Column(DateTime) 
    cancel_at_period_end = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    user = relationship("Profile", back_populates="subscriptions")