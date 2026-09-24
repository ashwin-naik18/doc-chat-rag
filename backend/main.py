from fastapi import FastAPI, HTTPException, Depends
from model_manager import get_llm
from config import AVAILABLE_MODELS
from model import *
from database import Base, engine, get_db
import model 
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime
from sqlalchemy import select
from langchain_core.messages import HumanMessage, AIMessage

app = FastAPI(
    title= "AshRAG", 
    description="Local rag application",
    version="1.0.0"
)

Base.metadata.create_all(bind = engine)


@app.get("/root")
async def root():
    return {
        "message" : "AshRAG Backend is running.."
    }
    

@app.get("/get_models")
def get_models():
    return {
        "Available Models" : AVAILABLE_MODELS
    }
    

@app.post("/chat", response_model = ChatResponse)
async def chat(
    request : ChatRequest,
    db : Session = Depends(get_db)
    ):
    
    current_conversation_id  = request.conversation_id
    
    if request.conversation_id is None:
        con_id = str(uuid4())
        current_conversation_id  = request.conversation_id = con_id
        
        title = "New Chat"
        
        conversation = Conversation(
            id = con_id,
            title = title,
            created_at = datetime.now(),
            updated_at = datetime.now()
        )
        
        db.add(conversation)
        
        db.commit() 
        
    prev_conversation = db.get(
        Conversation,
        current_conversation_id
    )
    
    
    if prev_conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation Not Found"
        )
    
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code= 400,
            detail="Invalid Model Selected.."
        )
        
        
    message = model.Message(
        id = str(uuid4()),
        conversation_id = request.conversation_id,
        role = "User",
        content = request.message,
        model = AVAILABLE_MODELS[request.model],
        created_at = datetime.now()
    )
    
    stmt = (
        select(Message)
        .where(Message.conversation_id == current_conversation_id)
        .order_by(Message.created_at.desc())
        .limit(4)
    )
    
    recent_messages = db.scalars(stmt).all()
    
    recent_messages.reverse()
    
    
    db.add(message)
    
    db.commit()
    
    message_list = []
    
    for m in recent_messages:
        if m.role == "User":
            message_list.append(HumanMessage(m.content))
            
        if m.role == "Assistant":
            message_list.append(AIMessage(m.content))
            
    message_list.append(HumanMessage(request.message))
        
        
    try:
        
        llm = get_llm(request.model)
        
        response = await llm.ainvoke(
            message_list
        )
        
        ai_message = Message(
            id = str(uuid4()), 
            conversation_id = current_conversation_id,
            role = "Assistant", 
            content = response.content,
            model = AVAILABLE_MODELS[request.model],
            created_at = datetime.now()
        )
        
        prev_conversation.updated_at = datetime.now()

        db.add(ai_message)
        
        db.commit()
        
        return ChatResponse(
            model = AVAILABLE_MODELS[request.model],
            message= response.content,
            current_con_id= current_conversation_id
        )
    
    except Exception as e:
        
        raise HTTPException(
            status_code = 500,
            detail = f"Internal Server Error : {str(e)}"
        )
        
        
@app.get("/conversations", response_model= list[ConversatioResponse])
async def create_conversations(
    db: Session = Depends(get_db)
):
    query = (
        select(Conversation)
        .order_by(Conversation.updated_at.desc())
    )
    
    conversations = db.scalars(query).all()
    
    return conversations