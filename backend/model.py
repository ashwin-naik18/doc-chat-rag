from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, ForeignKey, String, DateTime, Enum
from database import Base
from sqlalchemy.orm import relationship
from datetime import datetime


class ChatRequest(BaseModel):
    conversation_id : str | None = None
    model : str
    message : str   
    
    
class ChatResponse(BaseModel):
    model : str
    message : str
    current_con_id : str
    

class Conversation(Base):
    __tablename__ = "conversation"


    id = Column(String, primary_key= True)
    user_id = Column(String, ForeignKey("users.id"))
    title = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    message = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )
    
    users = relationship(
        "User",
        back_populates="conversation"
    )
    
    documetns = relationship(
        "Document",
        back_populates="conversation",
        cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "message"
    
    id = Column(String, primary_key= True)
    conversation_id = Column(
        String, ForeignKey("conversation.id", ondelete = "CASCADE")
    )
    role = Column(
        String, Enum('User', 'Assistant')
    )
    content = Column(String)
    model = Column(String)
    created_at = Column(DateTime)
    
    conversation = relationship(
        "Conversation",
        back_populates="message"
    )
    
    
class ConversatioResponse(BaseModel):
    id : str
    title : str
    created_at : datetime
    updated_at : datetime
    
    model_config = ConfigDict(from_attributes= True)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    created_at = Column(DateTime)
    
    conversations = relationship(
        "Conversation",
        back_populates="user"
    )
    

class UserCreate(BaseModel):
    email : str
    name : str
    password : str
    confirm_password : str
    

class UserResponse(BaseModel):
    id : str
    name : str
    email : str
    created_at : datetime
    
    
class LoginRequest(BaseModel):
    email : str
    password : str
    

class TokenResponse(BaseModel):
    access_token : str
    token_type : str
    

class MessageResponse(BaseModel):
    id : str
    role : str
    content : str
    model : str | None
    created_at : datetime
    
    model_config = ConfigDict(from_attributes=True)
    

class ConversationDetailResponse(BaseModel):
    id : str
    title : str
    created_at : datetime
    updated_at : datetime
    messges = list[MessageResponse]
    
    model_config = ConfigDict(from_attributes=True)
    
    
class Document(Base):
    __tabelname__ = "documents"
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"))
    conversation_id = Column(String, ForeignKey("conversation.id", ondelete="CASCADE"))
    filename = Column(String)
    filepath = Column(String)
    content_type = Column(String)
    created_at = Column(DateTime)
    
    conversation = relationship(
        "Conversation",
        back_populates="documents"
    )
    

class DocumentResponse(BaseModel):
    id : str
    filename : str
    content_type : str
    created_at : datetime
    
    model_config = ConfigDict(from_attributes=True)