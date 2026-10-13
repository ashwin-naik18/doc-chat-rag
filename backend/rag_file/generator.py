from .retriever import retrive_chunk
from model_manager import get_llm
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

parser = StrOutputParser()

rewrite_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Given the chat history and the user's latest question,
        rewrite the latest question as a standalone question that
        can be understood without the chat history.
        Do NOT answer the question.
        If it is already standalone, return it unchanged.
        Return only the question.
        """
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])

answer_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        """
        Use ONLY the information below to answer.

        Context:
        {chunks}

        If the answer isn't present, say you don't know.
        """
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{question}")
])


def generate_answer(user_id, conversation_id, query, model_name, chat_history=None):
    chat_history = chat_history or []
    llm = get_llm(model_name=model_name)

    search_query = query

    if chat_history:
        rewritten = (rewrite_prompt | llm | parser).invoke(
            {"chat_history": chat_history, "question": query}
        ).strip()

        if rewritten:
            search_query = rewritten

    docs = retrive_chunk(user_id, conversation_id, search_query)
    context = "\n\n".join(d.page_content for d in docs)

    chain = answer_prompt | llm | parser

    return chain.invoke(
        {
            "chunks": context,
            "chat_history": chat_history,
            "question": query
        }
    )