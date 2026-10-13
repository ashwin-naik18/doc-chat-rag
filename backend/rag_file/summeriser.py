from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from model_manager import get_llm
from .vectorstore import get_document_chunk

MAX_BATCH_CHARS = 6000
MAX_REDUCE_ROUNDS = 5


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


def _batch_texts(texts, max_chars=MAX_BATCH_CHARS):
    batches, current, size = [], [], 0

    for t in texts:
        if current and size + len(t) > max_chars:
            batches.append("\n\n".join(current))
            current, size = [], 0
        current.append(t)
        size += len(t)

    if current:
        batches.append("\n\n".join(current))

    return batches


def summarize_document(user_id, conversation_id, document_id, model_name):
    chunks = get_document_chunk(user_id, conversation_id, document_id)

    if not chunks:
        return "I couldn't find any content for this document."

    llm = get_llm(model_name)
    section_chain = chunk_summary_prompt | llm | StrOutputParser()
    final_chain = final_summary_prompt | llm | StrOutputParser()

    texts = [text for text, _ in chunks]

    summaries = [
        section_chain.invoke({"chunk_text": batch})
        for batch in _batch_texts(texts)
    ]


    rounds = 0
    while (
        len("\n\n".join(summaries)) > MAX_BATCH_CHARS
        and len(summaries) > 1
        and rounds < MAX_REDUCE_ROUNDS
    ):
        summaries = [
            section_chain.invoke({"chunk_text": batch})
            for batch in _batch_texts(summaries)
        ]
        rounds += 1

    return final_chain.invoke({"summaries": "\n\n".join(summaries)})