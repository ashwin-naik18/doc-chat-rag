from .retriever import retrive_chunk
from model_manager import get_llm
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

parser = StrOutputParser()

def generate_answer(user_id, conversation_id, query, model_name):
    chunks = retrive_chunk(user_id, conversation_id, query)
    
    chunks = "\n\n".join([c.page_content for c in chunks])
    
    llm = get_llm(model_name=model_name)
    
    prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Use ONLY the information below to answer.

        Context:
        {chunks}

        If the answer isn't present, say you don't know.
        """
        ),
        ("human", "{question}")
    ])
    
    chain = prompt | llm | parser

    result = chain.invoke(
        {
            "chunks" :  chunks,
            "question" : query
        }
    )
    
    return result