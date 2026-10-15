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
from rag_file.generator import generate_answer
from rag_file.vectorstore import add_chunk, delete_document_chunks
from rag_file.loader import chunk_documents, load_pdf
from rag_file.router import router_query
from rag_file.summeriser import summarize_document
from starlette.concurrency import run_in_threadpool
import logging 
from rag_file.vectorstore import add_chunk, delete_document_chunks, delete_conversation_chunks
from fastapi.middleware.cors import CORSMiddleware


logger = logging.getLogger(__name__)




app = FastAPI(
    title= "AshRAG", 
    description="Local rag application",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"]
)

Base.metadata.create_all(bind = engine)


def get_current_user(
    credentials = Depends(security.oauth_scheme),
    db : Session = Depends(get_db)
) :
    token = credentials.credentials
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
    
    if request.model not in AVAILABLE_MODELS:
        raise HTTPException(
            status_code= 400,
            detail="Invalid Model Selected.."
        )
        
        
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
    
        
    if prev_conversation.title == "New Chat":
        prev_conversation.title = request.message.strip()[:40] or "New Chat"
    
        
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
        
        
        documents_stmt = select(Document).where(
            Document.user_id == current_user.id,
            Document.conversation_id == current_conversation_id
        )
        conversation_documents = db.scalars(documents_stmt).all()

        if not conversation_documents:
            llm = get_llm(request.model)
            response = await llm.ainvoke(message_list)
            answer_text = response.content

        else:
            route = await run_in_threadpool(
                router_query,
                request.message,
                message_list[:-1]
            )

            if route == "GENERAL":
                llm = get_llm(request.model)
                response = await llm.ainvoke(message_list)
                answer_text = response.content

            elif route == "DOCUMENT_QA":
                answer_text = await run_in_threadpool(
                generate_answer,
                current_user.id,
                current_conversation_id,
                request.message,
                request.model,  
                message_list[:-1]
            )

            elif route == "DOCUMENT_SUMMARY":
                query_lower = request.message.casefold()

                if len(conversation_documents) == 1:
                    selected_document = conversation_documents[0]
                else:
                    matches = [
                        doc for doc in conversation_documents
                        if doc.filename
                        and doc.filename.casefold() in query_lower
                    ]

                    selected_document = matches[0] if len(matches) == 1 else None

                if selected_document is None:
                    filenames = "\n".join(
                        f"- {doc.filename}" for doc in conversation_documents
                    )
                    answer_text = (
                        "Which PDF would you like me to summarize? "
                        "Please mention its filename:\n" + filenames
                    )
                else:
                    answer_text = await run_in_threadpool(
                        summarize_document,
                        current_user.id,
                        current_conversation_id,
                        selected_document.id,
                        request.model
                    )

        
        ai_message = Message(
            id = str(uuid4()), 
            conversation_id = current_conversation_id,
            role = "Assistant", 
            content = answer_text,
            model = AVAILABLE_MODELS[request.model],
            created_at = datetime.now()
        )
        
        prev_conversation.updated_at = datetime.now()

        db.add(ai_message)
        
        db.commit()
        
        return ChatResponse(
            model = AVAILABLE_MODELS[request.model],
            message= answer_text,
            current_con_id= current_conversation_id
        )
    
    except Exception as e:
        db.rollback()
        logger.exception("chat request failed")
        
        raise HTTPException(
            status_code = 500,
            detail = f"Internal Server Error"
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
            
        query = select(User).where(User.email == user.email.lower())
        
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
            email = user.email.lower(),
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
        print(str(e))
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
        query = select(User).where(User.email == user.email.lower())
        
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
        

MAX_UPLOAD_BYTES = 20 * 1024 * 1024  

def process_pdf(file_path, user_id, conversation_id, document_id):
    pages = load_pdf(file_path)
    chunks = chunk_documents(pages)
    add_chunk(user_id, conversation_id, document_id, chunks)        


@app.post("/conversations/{conversation_id}/documents", response_model=DocumentResponse)
async def upload_doc(
    conversation_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only pdf File supported")

    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")


    content = await file.read(MAX_UPLOAD_BYTES + 1)

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")

    document_id = str(uuid4())

    user_doc_dir = Path("data") / "documents" / str(current_user.id)
    user_doc_dir.mkdir(parents=True, exist_ok=True)

    file_path = user_doc_dir / f"{document_id}.pdf"
    file_path.write_bytes(content)

    try:
        await run_in_threadpool(
            process_pdf,
            file_path,
            current_user.id,
            conversation_id,
            document_id
        )

        document = Document(
            id=document_id,
            user_id=current_user.id,
            conversation_id=conversation_id,
            filename=file.filename,
            filepath=str(file_path),
            content_type=file.content_type,
            created_at=datetime.now()
        )

        db.add(document)
        db.commit()
        db.refresh(document)

    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        try:
            delete_document_chunks(document_id)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Failed to process PDF")

    return DocumentResponse(
        id=document_id,
        filename=file.filename,
        content_type=file.content_type,
        created_at=document.created_at
    )
    

@app.get("/conversations/{conversation_id}/documents", response_model=list[DocumentResponse])
def list_documents(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    stmt = (
        select(Document)
        .where(Document.conversation_id == conversation_id)
        .order_by(Document.created_at.asc())
    )

    return db.scalars(stmt).all()

@app.post("/conversations", response_model=ConversatioResponse, status_code=201)
def new_conversation(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    now = datetime.now()

    conversation = Conversation(
        id=str(uuid4()),
        user_id=current_user.id,
        title="New Chat",
        created_at=now,
        updated_at=now
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@app.delete("/conversations/{conversation_id}/documents/{document_id}", status_code=204)
def delete_document(
    conversation_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.get(Document, document_id)

    if (
        document is None
        or document.conversation_id != conversation_id
        or document.user_id != current_user.id
    ):
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = Path(document.filepath)

    db.delete(document)
    db.commit()

    file_path.unlink(missing_ok=True)

    try:
        delete_document_chunks(document_id)
    except Exception:
        logger.exception("Failed to delete vectors for document %s", document_id)
        
        
@app.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    conversation = db.get(Conversation, conversation_id)

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    file_paths = [Path(d.filepath) for d in conversation.documents]

    db.delete(conversation)  
    db.commit()

    for p in file_paths:
        p.unlink(missing_ok=True)

    try:
        delete_conversation_chunks(conversation_id)
    except Exception:
        logger.exception("Failed to delete vectors for conversation %s", conversation_id)