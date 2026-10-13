from rag_file.embeddings import embedding
from rag_file.loader import load_pdf, chunk_documents
from rag_file.vectorstore import add_chunk

pdf = load_pdf("C:\\Users\\ashwi\\OneDrive\\Desktop\\rag\\backend\\Resource_Booklet_Hack4SDG.pdf")

chunk = chunk_documents(pdf)

status = add_chunk(1, 2, 3, chunk)

print(status)
print(chunk[3])