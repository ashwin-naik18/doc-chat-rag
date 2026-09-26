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
import security
from jwt import InvalidTokenError
from fastapi import UploadFile, File
from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader


app = FastAPI(
    title= "AshRAG", 
    description="Local rag application",
    version="1.0.0"
)

Base.metadata.create_all(bind = engine)


def get_current_user(
    token : str = Depends(security.oauth_scheme),
    db : Session = Depends(get_db)
) :
    try:
        payload = security.jwt.decode(
            token,
            security.SECRET_KEY,
            algorithms=[security.ALGORITHM]
        )

        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Unauthorised"
            )
            
        user = db.get(User, user_id)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="User not found"
            )
            
        return user
    
    except HTTPException:
        raise
    
    except InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Unauthorised"
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail='Internal Server Error'
        )
    
    
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
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db)
    ):
    
    current_conversation_id  = request.conversation_id
    
    if request.conversation_id is None:
        con_id = str(uuid4())
        current_conversation_id  = request.conversation_id = con_id
        
        title = "New Chat"
        
        conversation = Conversation(
            id = con_id,
            user_id = current_user.id,
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
        
    if prev_conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this conversation"
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = (
        select(Conversation)
        .order_by(Conversation.updated_at.desc())
    ).where(Conversation.user_id == current_user.id)
    
    conversations = db.scalars(query).all()
    
    
    return conversations


@app.post("/register", response_model=UserResponse)
def register_user(
    user : UserCreate,
    db : Session = Depends(get_db)
) :
    try: 
        
        if user.password != user.confirm_password:
            raise HTTPException(
                status_code=422,
                detail= "password mismatch"
            )
            
        query = select(User).where(User.email == user.email)
        
        res = db.scalars(query).first()
        
        if res:
            raise HTTPException(
                status_code= 409,
                detail= "Conflict : User already exist"
            )
            
            
        hashed_password = security.hash_password(user.password)
        
        user_data = User(
            id = str(uuid4()),
            name = user.name,
            email = user.email,
            hashed_password = hashed_password,
            created_at = datetime.now()
        )
        
        db.add(user_data)
        
        db.commit()
        
        user_response = UserResponse(
            id=user_data.id,
            email=user_data.email,
            name=user_data.name,
            created_at=user_data.created_at
        )
        
        return user_response
    
    except HTTPException :
        raise 
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )
        
        
@app.post("/login", response_model=TokenResponse)
def login(
    user : LoginRequest,
    db : Session = Depends(get_db)
) :
    try: 
        query = select(User).where(User.email == user.email)
        
        res = db.scalars(query).first()
        
        if not res:
            raise HTTPException(
                status_code=401,
                detail="Invalid User"
            )
            
        if not security.verify_password(res.hashed_password, user.password):
            raise HTTPException(
                status_code=401,
                detail="Invalid Password"
            )
            
        jwt_token = security.create_access_token(
            data = {"sub" : str(res.id)}
        )
        
        return TokenResponse(
            access_token=jwt_token,
            token_type= "bearer"
        )
            
    except HTTPException:
        raise
    
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )
        

@app.get("/me")
def get_me(
    user : User = Depends(get_current_user)
) :
    return {
        "id" : user.id,
        "name" : user.name,
        "email" : user.email
    }
    

@app.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_con_msg(
    conversation_id : str,
    current_user : User = Depends(get_current_user),
    db : Session = Depends(get_db)
) :
    try:
        conversations = db.get(Conversation, conversation_id)
        
        if conversations is None:
            raise HTTPException(
                status_code=404,
                detail="No Conversation found"
            )
        
        if conversations.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail= "Unauthonticated"
            )
            
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        
        messaeges = db.scalars(stmt).all()
        
        return ConversationDetailResponse(
            id=conversations.id,
            title=conversations.title,
            created_at=conversations.created_at,
            updated_at=conversations.updated_at,
            messges = messaeges
        )
    
    except HTTPException :
        raise
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal Server Error"
        )
        

@app.post("/conversations/{conversation_id}/documents", response_model=DocumentResponse)
async def upload_doc(
    conversation_id : str,
    file : UploadFile,
    db : Session = Depends(get_db),
    current_user : User = Depends(get_current_user)
) :
    if file.content_type != "application/pdf" :
        raise HTTPException(
            status_code=400,
            detail="Only pdf File supported"
        )
        
    conversation = db.get(Conversation, conversation_id)
    
    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )
        
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=401,
            detail="Unauthorised"
        )
        
    document_id = str(uuid4())
    
    user_doc_dir = Path("data") / "documents" / str(current_user.id)
    user_doc_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = user_doc_dir / f"{document_id}.pdf"
    
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    document = Document(
        id = document_id,
        user_id = current_user.id,
        conversation_id = conversation_id,
        filename = file.filename,
        filepath = str(file_path),
        content_type = file.content_type,
        created_at = datetime.now()
    )
    
    db.add(document)
    
    db.commit()
    
    db.refresh(document)
    
    return DocumentResponse(
        id=document_id,
        filename=file.filename,
        content_type=file.content_type,
        created_at=document.created_at
    )
