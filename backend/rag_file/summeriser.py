from langchain_core.prompts import ChatPromptTemplate
from .router import router_llm
from langchain_core.output_parsers import StrOutputParser
from .vectorstore import get_document_chunk


chunk_summary_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Summarize the provided document section.
        Preserve its important facts, concepts, definitions,
        examples, and technical details.
        Do not introduce information that is not present
        in the provided section.
        """
    ),
    ("human", "{chunk_text}")
])


final_summary_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Create a coherent, well-organized explanation of
        the document using the partial summaries provided.

        Preserve the main ideas, important details, and
        relationships between concepts. Remove repetition.
        Do not invent facts or omit major topics.
        Organize the explanation with useful headings.
        """
    ),
    ("human", "{summaries}")
])

chain1 = chunk_summary_prompt | router_llm | StrOutputParser()
chain2 = final_summary_prompt | router_llm | StrOutputParser()

def summarize_document(user_id, conversation_id, document_id):
    chunks = get_document_chunk(user_id, conversation_id, document_id)
    
    partial_summary = ""
    
    for chunk_text, metadata in chunks:
        r = chain1.invoke(
            {
                "chunk_text" : chunk_text
            }
        )
        
        partial_summary += f"\n{r}"
        
    
    
    final_result = chain2.invoke(
        {
            "summaries" : partial_summary
        }
    )
    
    return final_result