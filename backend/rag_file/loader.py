from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_pdf(file_path):
    path = Path(file_path)
    
    loader = PyPDFLoader(str(path))
    
    document = loader.load()
    
    return document


def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 2000,
        chunk_overlap = 100
    )
    
    chunks = splitter.split_documents(documents)
    
    return chunks

