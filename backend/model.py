from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, String, DateTime, Enum
from database import Base
from sqlalchemy.orm import relationship


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
    title = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    
    message = relationship(
        "Message",
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
    
    
class ConversatioResponse(Base):
    id = Column(String, primary_key=True)
    title = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)