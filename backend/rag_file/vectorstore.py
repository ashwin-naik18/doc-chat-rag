from pathlib import Path
from .embeddings import embedding
from langchain_chroma import Chroma
from langchain_core.documents import Document

PROJECT_ROOT = Path(__file__).resolve().parents[2]
VECTORSTORE_DIR = PROJECT_ROOT / "vectorstore"

vector_db = Chroma(
    collection_name="doc-chat",\
    embedding_function=embedding,
    persist_directory=str(VECTORSTORE_DIR)
)


def add_chunk(user_id, conversation_id, document_id, chunks):
    doc_with_metadata = []
    
    for i, c in enumerate(chunks):
        c.metadata = {
            **c.metadata,
            "chunk_id" : i,
            "user_id" : user_id,
            "conversation_id" : conversation_id,
            "document_id" : document_id
        }
        
        doc_with_metadata.append(c)
        
    vector_db.add_documents(
        documents=doc_with_metadata,
        embedding = embedding
    )
    
    return True


def get_conversation_chunk(user_id, conversation_id):
    result = vector_db.get(
        where={
            "$and" : [
                {"user_id" : user_id},
                {"conversation_id" : conversation_id}
            ]
        },
        include=['documents', 'metadatas']
    )
    
    chunk_with_metadata = list(zip(
        result['documents'],
        result['metadatas']
    ))
    
    chunk_with_metadata.sort(
        key=lambda item :(
            item[1]['document_id'],
            item[1]['chunk_id']
        )
    )
    

def get_document_chunk(user_id, conversation_id, document_id):
    result = vector_db.get(
        where={
            "$and" : [
                {'document_id' : document_id},
                {'user_id' : user_id},
                {'conversation_id' : conversation_id}
            ]
        }, 
        include=['documents', 'metadatas']
    )
    
    chunk_with_metadata = list(zip(
        result['documents'],
        result['metadatas']
    ))
    
    chunk_with_metadata.sort(
        key= lambda item : (
            item[1]['chunk_id']
        )
    )
    
    return chunk_with_metadata