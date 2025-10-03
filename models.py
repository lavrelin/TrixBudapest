from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Boolean, Text, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

class Gender(enum.Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class PostStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = 'users'
    
    id = Column(BigInteger, primary_key=True)  # ИЗМЕНЕНО: BigInteger для Telegram ID
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    gender = Column(Enum(Gender), default=Gender.UNKNOWN)
    referral_code = Column(String(255), unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False)
    category = Column(String(255))
    subcategory = Column(String(255))
    text = Column(Text)
    media = Column(JSON, default=list)  # ИСПРАВЛЕНО: default=list
    hashtags = Column(JSON, default=list)  # ИСПРАВЛЕНО: default=list
    anonymous = Column(Boolean, default=False)
    status = Column(Enum(PostStatus), default=PostStatus.PENDING)
    moderation_message_id = Column(BigInteger)  # ИСПРАВЛЕНО: BigInteger для больших ID
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Piar specific fields
    is_piar = Column(Boolean, default=False)
    piar_name = Column(String(255), nullable=True)
    piar_profession = Column(String(255), nullable=True)
    piar_districts = Column(JSON, default=list, nullable=True)
    piar_phone = Column(String(255), nullable=True)
    piar_instagram = Column(String(255), nullable=True)  
    piar_telegram = Column(String(255), nullable=True)   
    piar_price = Column(String(255), nullable=True)
    piar_description = Column(Text, nullable=True)  # ДОБАВЛЕНО: отдельное поле для описания
