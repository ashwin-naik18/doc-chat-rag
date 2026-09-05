from langchain_ollama import ChatOllama
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

parser = StrOutputParser()

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


llm = ChatOllama(model="llama3.1:8b")

embedding_model = HuggingFaceEmbeddings(
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
)

text = """
    The Armor of Genius: An Essay on Iron Man**

    In a world where superheroes are the norm, Tony Stark stands out as one of the most iconic figures.
    Known to the world as Iron Man, he is a billionaire inventor and philanthropist who has dedicated his life to protecting humanity from various threats.
    Born into a wealthy family, Tony Stark inherited his father's genius-level intellect and business acumen.

    However, it was after being kidnapped by terrorists in Afghanistan that he created the first Iron Man suit.
    The suit's primary function is to protect its wearer from harm, but it also features advanced artificial intelligence, repulsor technology, and a suite of sophisticated sensors.
    As Iron Man, Tony has battled some of the most formidable villains in the Marvel universe, including Ultron, Thanos, and Loki.
    His arsenal includes an array of cutting-edge suits, each designed to tackle specific challenges.
    The Mark XLVII suit, for instance, is capable of flight, while the Mark LXX features advanced artificial intelligence.

    Tony's genius-level intellect also extends beyond his inventions. He has a quick wit and sharp tongue, often using humor to defuse tense situations.
    However, beneath this façade lies a complex individual grappling with the moral implications of his actions as Iron Man.

    The weight of responsibility for saving the world can be crushing at times.
    Despite the risks involved, Tony remains committed to his mission.
    He is driven by a sense of duty and a desire to leave the world a better place than he found it.
    As the self-proclaimed "Genius, Billionaire, Playboy, Philanthropist,"
    Iron Man has earned a reputation as one of the most formidable superheroes in the Marvel universe.

    In conclusion, Tony Stark's legacy as Iron Man is built on a foundation of innovation, bravery, and sacrifice.
    His commitment to protecting humanity from harm continues to inspire awe and admiration around the world.

"""

docs = [Document(page_content=text, metadata = {"source" : "Ashwin", "DocId" : "A001"})]

# print(docs)

splitter = RecursiveCharacterTextSplitter(
    chunk_size = 300,
    chunk_overlap = 50
)

chunks = splitter.split_documents(docs)

print(f"Total chunks : {len(chunks)}")

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embedding_model
)

search = vector_store.as_retriever(
    search_kwargs={"k" : 3}
)

result = search.invoke("who is iron man")

contents = "\n\n".join([c.page_content for c in result])

chain = prompt | llm | parser

final = chain.invoke({
    "info" : contents,
    "question" : "who is iron man"
})

print(final)

