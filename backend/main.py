from fastapi import FastAPI, HTTPException, Depends
from model_manager import get_llm
from config import AVAILABLE_MODELS
from model import *
from database import Base, engine, get_db
import model 
from sqlalchemy.orm import Session
from uuid import uuid4
from datetime import datetime

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
    
    if request.conversation_id is None:
        con_id = str(uuid4())
        request.conversation_id = con_id
        
        title = "New Chat"
        
        conversation = Conversation(
            id = con_id,
            title = title,
            created_at = datetime.now(),
            updated_at = datetime.now()
        )
        
        db.add(conversation)
        
        db.commit() 
    
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code= 400,
            detail="Invalid Model Selected.."
        )
        
        
    try:
        llm = get_llm(request.model)
        
        response = await llm.ainvoke(
            request.message
        )

        
        return ChatResponse(
            model = AVAILABLE_MODELS[request.model],
            message= response.content
        )
    
    except Exception as e:
        
        raise HTTPException(
            status_code = 500,
            detail = f"Internal Server Error : {str(e)}"
        )
        
        
@app.post("/conversations")
async def create_conversations(
    db: Session = Depends(get_db)
):
    conversation = model.Conversation(
        
    )
    
    