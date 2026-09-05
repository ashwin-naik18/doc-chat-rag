from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()

loader = PyPDFLoader("Build_Your_Own_LLM_Handbook.pdf") # load 

docs = loader.load()


# print(len(docs))
# print(type(docs))

splitter = RecursiveCharacterTextSplitter( 
    chunk_size = 1000,
    chunk_overlap = 50
)

chunk = splitter.split_documents(docs) 

# print(len(chunk))

embedding_model = HuggingFaceEmbeddings(model_name = "sentence-transformers/all-MiniLM-L6-v2")

vector_store = Chroma.from_documents(
    documents=chunk,
    embedding=embedding_model
)

search = vector_store.as_retriever(
    search_kwargs = {"k" : 3} 
)

user = input("Enter Your Question : ")

content = search.invoke(user)

content = "\n\n".join([c.page_content for c in content])

llm = ChatOllama(model="llama3.1:8b")

prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
    Use ONLY the information below to answer.

    Context:
    {info}

    If the answer isn't present, say you don't know.
    """
    ),
    ("human", "{question}")
])

chain = prompt | llm | parser | parser

res = chain.invoke({
    "info" : content,
    "question" : user
})

# 

print(content)
print()
print()
print(res)
