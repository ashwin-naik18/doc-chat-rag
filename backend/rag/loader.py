from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_pdf(file_path):
    path = Path(file_path)
    
    loader = PyPDFLoader(str(path))
    
    document = loader.load()
    
    print(len(document))
    print(document[0].page_content[:50])
    
    return document


def chunk_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 2000,
        chunk_overlap = 100
    )
    
    chunks = splitter.split_documents(documents)
    
    return chunks

print("content : ")
print(chunk_documents(load_pdf("C:\\Users\\ashwi\\OneDrive\\Desktop\\rag\\backend\\rag\\MODULE 2_DAA.pdf"))[3].page_content)