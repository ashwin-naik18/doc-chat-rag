# Doc Chat RAG

A local Retrieval-Augmented Generation (RAG) application built with FastAPI, LangChain, Ollama, and SQLite.

Doc Chat RAG is a learning-focused AI application designed to combine local language models, persistent conversations, model switching, and document-based retrieval into a single platform.

## Overview

Doc Chat RAG provides a conversational AI interface using locally hosted models through Ollama.

The application supports multiple models and allows users to switch between them while continuing the same conversation. Conversation data is persisted using SQLite and SQLAlchemy.

The planned RAG pipeline will allow users to upload documents, process their content, create embeddings, retrieve relevant information, and generate context-aware responses.

## Current Features

* FastAPI backend
* LangChain integration
* Ollama integration
* Support for multiple local models

  * `llama3.1:8b`
  * `qwen2.5-coder:14b`
* Model switching within the same conversation
* Persistent conversation storage
* Persistent message storage
* SQLite database
* SQLAlchemy ORM
* Conversation history
* Recent message retrieval
* LangChain `HumanMessage` and `AIMessage` integration
* Pydantic request and response validation
* Conversation activity tracking using `updated_at`

## Architecture

```text
                         Client
                           |
                           v
                    +-------------+
                    |   FastAPI   |
                    +------+------+
                           |
          +----------------+----------------+
          |                                 |
          v                                 v
 +-------------------+             +-------------------+
 | Conversation      |             | LangChain         |
 | Management        |             |                   |
 +---------+---------+             | ChatOllama        |
           |                       +---------+---------+
           v                                 |
 +-------------------+              +--------+--------+
 | SQLAlchemy        |              |                 |
 +---------+---------+              v                 v
           |                  Llama 3.1 8B      Qwen Coder 14B
           v
     +-----------+
     |  SQLite   |
     +-----------+
```

## Conversation System

Each conversation is identified by a unique conversation ID.

A conversation can continue even when the selected model changes.

Example:

```text
Conversation A

User:
Explain Retrieval-Augmented Generation.

Assistant:
...

User:
What are embeddings?

Assistant:
...

Model switched from Llama 3.1 8B to Qwen Coder 14B

User:
Show me a Python implementation.

Assistant:
...
```

The messages belong to the same conversation regardless of which model generated the response.

## Chat History

The current implementation retrieves the most recent four messages from a conversation before generating a response.

The database messages are converted into LangChain message objects.

```text
Database Message
       |
       +---- user      -> HumanMessage
       |
       +---- assistant -> AIMessage
```

The current user message is then appended to the history before being passed to the selected model.

```text
Previous conversation messages
            +
Current user message
            |
            v
      LangChain messages
            |
            v
         ChatOllama
            |
            v
       Selected model
```

## Database Design

Doc Chat RAG currently uses two primary tables.

### Conversations

Stores metadata about each conversation.

```text
conversations
---------------
id
title
created_at
updated_at
```

### Messages

Stores individual messages belonging to a conversation.

```text
messages
---------------
id
conversation_id
role
content
model
created_at
```

Relationship:

```text
Conversation
     |
     +---- Message
     |
     +---- Message
     |
     +---- Message
```

The `conversation_id` column in the `messages` table references the corresponding conversation.

## Request Flow

```text
User Request
     |
     v
FastAPI /chat
     |
     v
Validate selected model
     |
     v
Check conversation ID
     |
     +---- New conversation
     |          |
     |          v
     |    Create conversation
     |
     +---- Existing conversation
                |
                v
        Retrieve conversation
                |
                v
        Retrieve recent messages
                |
                v
       Convert to LangChain messages
                |
                v
          Add current message
                |
                v
           ChatOllama
                |
                v
         Selected local model
                |
                v
         Save assistant response
                |
                v
             Return result
```

## Technology Stack

| Technology | Purpose                         |
| ---------- | ------------------------------- |
| Python     | Core programming language       |
| FastAPI    | Backend API framework           |
| LangChain  | LLM and message integration     |
| Ollama     | Local model execution           |
| SQLAlchemy | Object-relational mapping       |
| SQLite     | Persistent application database |
| Pydantic   | Data validation and API schemas |

## Project Structure

```text
doc-chat-rag/
|
+-- backend/
|   +-- main.py
|   +-- model.py
|   +-- db_models.py
|   +-- database.py
|   +-- model_manager.py
|   +-- config.py
|
+-- frontend/
|
+-- data/
|
+-- vectorstore/
|
+-- requirements.txt
+-- README.md
```

## Supported Models

The current implementation is configured to work with:

```text
llama3.1:8b
qwen2.5-coder:14b
```

The backend uses application-level model identifiers and maps them to the corresponding Ollama model names.

## Roadmap

### Backend

* [x] FastAPI setup
* [x] Ollama integration
* [x] LangChain integration
* [x] SQLAlchemy setup
* [x] SQLite database
* [x] Conversation model
* [x] Message model
* [x] Persistent conversation storage
* [x] Persistent message storage
* [x] Model switching
* [x] Conversation context
* [ ] Conversation history API
* [ ] Previous conversation retrieval
* [ ] Conversation title generation

### RAG Pipeline

* [ ] Document upload
* [ ] Document loading
* [ ] PDF processing
* [ ] Text extraction
* [ ] Text chunking
* [ ] Embedding generation
* [ ] Vector database integration
* [ ] Similarity search
* [ ] Retriever implementation
* [ ] RAG chain
* [ ] Source attribution

### Frontend

* [ ] Chat interface
* [ ] Model selector
* [ ] Conversation sidebar
* [ ] Previous conversation access
* [ ] Document upload interface
* [ ] Response streaming
* [ ] Loading and error states

## Goal

The goal of Doc Chat RAG is to build a complete local AI application while understanding the underlying components rather than relying entirely on high-level abstractions.

The planned architecture is:

```text
FastAPI
   |
   v
Conversation Management
   |
   v
LangChain
   |
   +---- Chat Models
   |
   +---- Document Processing
   |
   +---- Embeddings
   |
   +---- Retrieval
   |
   v
RAG Pipeline
   |
   v
Local Ollama Models
```

## Project Status

Current status: Backend conversation system in development.

The next milestone is implementing the conversation history API and integrating previous conversations into the web interface.
