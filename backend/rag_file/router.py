from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import config


router_llm = ChatOllama(
    model= config.ROUTER_MODEL,
    temperature=0
)


router_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        You are a query-routing classifier for a PDF chat application.

        Classify the user's latest message into exactly ONE of
        the following categories:

        1. GENERAL
        - Greetings and casual conversation.
        - Arithmetic and general knowledge unrelated to the PDF.
        - Questions that do not require document information.

        2. DOCUMENT_QA
        - Questions asking for specific information from an uploaded PDF.
        - Questions about particular concepts, facts, sections, or details.
        - Follow-up questions that depend on previously discussed PDF content.

        3. DOCUMENT_SUMMARY
        - Requests to summarize or explain the entire PDF.
        - Requests for a complete overview of the document.
        - Requests to explain the document chapter by chapter or section by section.
        - Requests to cover the document's overall content and key points.

        Use the conversation history to understand references and follow-up
        questions. Classify based on the user's latest message and its context.

        Do not answer the user's question.
        Do not provide explanations or additional text.

        Return exactly one of these labels:
        GENERAL
        DOCUMENT_QA
        DOCUMENT_SUMMARY
        """
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{query}")
])


router_chain = router_prompt | router_llm | StrOutputParser()


def router_query(query : str, chat_history: list) -> str:
    result = router_chain.invoke(
        {
            "chat_history" : chat_history,
            "query" : query
        }
    )
    
    result = result.strip().upper()
    
    if result not in {"DOCUMENT_QA", 'GENERAL', "DOCUMENT_SUMMARY"} :
        return "GENERAL"
    
    return result