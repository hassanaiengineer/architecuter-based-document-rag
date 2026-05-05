# from fastapi import APIRouter, HTTPException, Path, Query, Depends
# from pydantic import BaseModel, Field
# from typing import List, Dict, Any, Optional
# import re
# import pandas as pd
# from utils.embedding import DocumentProcessor
# from utils.language_model import LanguageModel
# import os
# import json
# from routers.documents import document_store

# router = APIRouter()

# # Initialize language model
# language_model = LanguageModel()


# class QueryRequest(BaseModel):
#     question: str = Field(..., description="The question to ask about the document")
#     max_tokens: int = Field(1000, description="Maximum tokens for the response")
#     top_k: int = Field(4, description="Number of similar document chunks to retrieve")


# class QueryResponse(BaseModel):
#     document_id: str
#     question: str
#     answer: str
#     input_tokens: Optional[int] = None
#     output_tokens: Optional[int] = None
#     chunks_used: Optional[int] = None
#     has_table: bool = False
#     table_data: Optional[List[Dict[str, Any]]] = None
#     table_title: Optional[str] = None


# def parse_markdown_table(markdown_text):
#     """Parse a markdown table string into a list of dictionaries."""
#     header_pattern = r"\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
#     header_match = re.search(header_pattern, markdown_text)
    
#     if not header_match:
#         return None
    
#     # Extract rows
#     table_pattern = r"\|\s*(\S+[^|]*)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
#     matches = re.findall(table_pattern, markdown_text)
    
#     matches = [match for match in matches if not all('-' in cell for cell in match)]
    
#     if not matches:
#         return None
        
#     # Extract header names (usually the first row)
#     headers = [h.strip() for h in header_match.groups()]
    
#     # Create table data
#     data = []
#     for match in matches:
#         row_data = {}
#         for i, cell in enumerate(match):
#             if i < len(headers):
#                 row_data[headers[i]] = cell.strip()
#         data.append(row_data)
    
#     return data


# def is_schedule_request(message):
#     """Determine if a message contains a request for schedule data."""
#     schedule_keywords = [
#         'door schedule', 'window schedule', 'fixture schedule', 'equipment schedule',
#         'room schedule', 'finish schedule', 'hardware schedule', 'light fixture schedule',
#         'plumbing fixture schedule', 'table', 'schedule', 'tabular'
#     ]
    
#     message_lower = message.lower()
#     return any(keyword in message_lower for keyword in schedule_keywords)


# def get_document_processor(document_id: str):
#     """Get a document processor for a specific document ID."""
#     if document_id not in document_store:
#         raise HTTPException(status_code=404, detail="Document not found")
    
#     doc_info = document_store[document_id]
    
#     if doc_info["status"] != "completed":
#         raise HTTPException(
#             status_code=400, 
#             detail=f"Document processing is {doc_info['status']}. Cannot query yet."
#         )
    
#     json_path = doc_info.get("structured_json_path")
#     if not json_path or not os.path.exists(json_path):
#         raise HTTPException(status_code=404, detail="Document data not found")
    
#     try:
#         return DocumentProcessor(json_path)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error loading document: {str(e)}")


# @router.post("/{document_id}/ask", response_model=QueryResponse)
# async def ask_question(
#     query: QueryRequest,
#     document_id: str = Path(..., description="The ID of the document to query"),
# ):
#     """Ask a question about a specific document"""
#     doc_processor = get_document_processor(document_id)
    
#     # Search for similar document chunks
#     similar_docs = doc_processor.search_similar_documents(query.question, k=query.top_k)
    
#     # Generate answer using the language model
#     answer_data = language_model.search_and_answer(
#         query.question, 
#         similar_docs, 
#         max_tokens=query.max_tokens
#     )
    
#     # Check if the query is asking for schedule data
#     is_schedule = is_schedule_request(query.question)
#     table_data = None
#     table_title = "Schedule"
    
#     # If answer contains a markdown table, parse it
#     has_table = "| " in answer_data["answer"] and " |" in answer_data["answer"] and is_schedule
#     if has_table:
#         # Try to extract title for the table
#         title_match = re.search(r"#+\s*(.*?schedule|.*?table)", answer_data["answer"], re.IGNORECASE)
#         if title_match:
#             table_title = title_match.group(1).strip()
        
#         # Parse table
#         table_data = parse_markdown_table(answer_data["answer"])
    
#     return QueryResponse(
#         document_id=document_id,
#         question=query.question,
#         answer=answer_data["answer"],
#         input_tokens=answer_data.get("input_tokens"),
#         output_tokens=answer_data.get("output_tokens"),
#         chunks_used=len(similar_docs),
#         has_table=has_table,
#         table_data=table_data,
#         table_title=table_title if has_table else None
#     )


# class ChatHistoryEntry(BaseModel):
#     role: str
#     content: str
#     timestamp: str
#     has_table: Optional[bool] = False
#     table_data: Optional[List[Dict[str, Any]]] = None
#     table_title: Optional[str] = None


# class ChatHistoryResponse(BaseModel):
#     document_id: str
#     history: List[ChatHistoryEntry]


# # In-memory chat history store
# # In production, you might want to use a database
# chat_history_store = {}


# @router.post("/{document_id}/chat", response_model=ChatHistoryEntry)
# async def chat_with_document(
#     query: QueryRequest,
#     document_id: str = Path(..., description="The ID of the document to chat with"),
# ):
#     """Chat with a document - maintains conversation history"""
#     # Initialize chat history for this document if it doesn't exist
#     if document_id not in chat_history_store:
#         chat_history_store[document_id] = []
    
#     # Add user message to chat history
#     import time
#     timestamp = time.strftime("%H:%M:%S")
    
#     chat_history_store[document_id].append(
#         ChatHistoryEntry(
#             role="user",
#             content=query.question,
#             timestamp=timestamp
#         )
#     )
    
#     # Get response using the same logic as ask_question
#     doc_processor = get_document_processor(document_id)
#     similar_docs = doc_processor.search_similar_documents(query.question, k=query.top_k)
#     answer_data = language_model.search_and_answer(query.question, similar_docs, max_tokens=query.max_tokens)
    
#     # Check for table data
#     is_schedule = is_schedule_request(query.question)
#     table_data = None
#     table_title = "Schedule"
#     has_table = "| " in answer_data["answer"] and " |" in answer_data["answer"] and is_schedule
    
#     if has_table:
#         # Try to extract title for the table
#         title_match = re.search(r"#+\s*(.*?schedule|.*?table)", answer_data["answer"], re.IGNORECASE)
#         if title_match:
#             table_title = title_match.group(1).strip()
        
#         # Parse table
#         table_data = parse_markdown_table(answer_data["answer"])
    
#     # Create assistant response entry
#     assistant_entry = ChatHistoryEntry(
#         role="assistant",
#         content=answer_data["answer"],
#         timestamp=time.strftime("%H:%M:%S"),
#         has_table=has_table,
#         table_data=table_data,
#         table_title=table_title if has_table else None
#     )
    
#     # Add to chat history
#     chat_history_store[document_id].append(assistant_entry)
    
#     return assistant_entry


# @router.get("/{document_id}/chat/history", response_model=ChatHistoryResponse)
# async def get_chat_history(
#     document_id: str = Path(..., description="The ID of the document"),
# ):
#     """Get the chat history for a specific document"""
#     if document_id not in document_store:
#         raise HTTPException(status_code=404, detail="Document not found")
    
#     history = chat_history_store.get(document_id, [])
    
#     return ChatHistoryResponse(
#         document_id=document_id,
#         history=history
#     )


# @router.delete("/{document_id}/chat/history")
# async def clear_chat_history(
#     document_id: str = Path(..., description="The ID of the document"),
# ):
#     """Clear the chat history for a specific document"""
#     if document_id not in document_store:
#         raise HTTPException(status_code=404, detail="Document not found")
    
#     if document_id in chat_history_store:
#         chat_history_store[document_id] = []
    
#     return {"message": "Chat history cleared successfully"}

# from fastapi import APIRouter, HTTPException, Path, Query, Depends
# from pydantic import BaseModel, Field
# from typing import List, Dict, Any, Optional
# import re
# import pandas as pd
# from utils.embedding import DocumentProcessor
# from utils.language_model import LanguageModel
# import os
# import json
# from routers.documents import document_store

# router = APIRouter()

# # Initialize language model
# language_model = LanguageModel()


# class QueryRequest(BaseModel):
#     question: str = Field(..., description="The question to ask about the document")
#     max_tokens: int = Field(1000, description="Maximum tokens for the response")
#     top_k: int = Field(4, description="Number of similar document chunks to retrieve")


# class QueryResponse(BaseModel):
#     document_id: str
#     question: str
#     answer: str
#     input_tokens: Optional[int] = None
#     output_tokens: Optional[int] = None
#     chunks_used: Optional[int] = None
#     has_table: bool = False
#     table_data: Optional[List[Dict[str, Any]]] = None
#     table_title: Optional[str] = None


# def parse_markdown_table(markdown_text):
#     """Parse a markdown table string into a list of dictionaries."""
#     header_pattern = r"\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
#     header_match = re.search(header_pattern, markdown_text)
    
#     if not header_match:
#         return None
    
#     # Extract rows
#     table_pattern = r"\|\s*(\S+[^|]*)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|"
#     matches = re.findall(table_pattern, markdown_text)
    
#     matches = [match for match in matches if not all('-' in cell for cell in match)]
    
#     if not matches:
#         return None
        
#     # Extract header names (usually the first row)
#     headers = [h.strip() for h in header_match.groups()]
    
#     # Create table data
#     data = []
#     for match in matches:
#         row_data = {}
#         for i, cell in enumerate(match):
#             if i < len(headers):
#                 row_data[headers[i]] = cell.strip()
#         data.append(row_data)
    
#     return data


# def is_schedule_request(message):
#     """Determine if a message contains a request for schedule data."""
#     schedule_keywords = [
#         'door schedule', 'window schedule', 'fixture schedule', 'equipment schedule',
#         'room schedule', 'finish schedule', 'hardware schedule', 'light fixture schedule',
#         'plumbing fixture schedule', 'table', 'schedule', 'tabular'
#     ]
    
#     message_lower = message.lower()
#     return any(keyword in message_lower for keyword in schedule_keywords)


# def get_document_processor(document_id: str):
#     """Get a document processor for a specific document ID."""
#     if document_id not in document_store:
#         raise HTTPException(status_code=404, detail="Document not found")
    
#     doc_info = document_store[document_id]
    
#     if doc_info["status"] != "completed":
#         raise HTTPException(
#             status_code=400, 
#             detail=f"Document processing is {doc_info['status']}. Cannot query yet."
#         )
    
#     json_path = doc_info.get("structured_json_path")
#     if not json_path or not os.path.exists(json_path):
#         raise HTTPException(status_code=404, detail="Document data not found")
    
#     try:
#         return DocumentProcessor(json_path)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error loading document: {str(e)}")


# @router.post("/{document_id}/ask", response_model=QueryResponse)
# async def ask_question(
#     query: QueryRequest,
#     document_id: str = Path(..., description="The ID of the document to query"),
# ):
#     """Ask a question about a specific document"""
#     doc_processor = get_document_processor(document_id)
    
#     # Search for similar document chunks
#     similar_docs = doc_processor.search_similar_documents(query.question, k=query.top_k)
    
#     # Generate answer using the language model
#     answer_data = language_model.search_and_answer(
#         query.question, 
#         similar_docs, 
#         max_tokens=query.max_tokens
#     )
    
#     # Check if the query is asking for schedule data
#     is_schedule = is_schedule_request(query.question)
#     table_data = None
#     table_title = "Schedule"
    
#     # If answer contains a markdown table, parse it
#     has_table = "| " in answer_data["answer"] and " |" in answer_data["answer"] and is_schedule
#     if has_table:
#         # Try to extract title for the table
#         title_match = re.search(r"#+\s*(.*?schedule|.*?table)", answer_data["answer"], re.IGNORECASE)
#         if title_match:
#             table_title = title_match.group(1).strip()
        
#         # Parse table
#         table_data = parse_markdown_table(answer_data["answer"])
    
#     return QueryResponse(
#         document_id=document_id,
#         question=query.question,
#         answer=answer_data["answer"],
#         input_tokens=answer_data.get("input_tokens"),
#         output_tokens=answer_data.get("output_tokens"),
#         chunks_used=len(similar_docs),
#         has_table=has_table,
#         table_data=table_data,
#         table_title=table_title if has_table else None
#     )


# class ChatHistoryEntry(BaseModel):
#     role: str
#     content: str
#     timestamp: str
#     has_table: Optional[bool] = False
#     table_data: Optional[List[Dict[str, Any]]] = None
#     table_title: Optional[str] = None


# class ChatHistoryResponse(BaseModel):
#     document_id: str
#     history: List[ChatHistoryEntry]


# # In-memory chat history store
# # In production, you might want to use a database
# chat_history_store = {}


# @router.get("/{document_id}/chat/history", response_model=ChatHistoryResponse)
# async def get_chat_history(
#     document_id: str = Path(..., description="The ID of the document"),
# ):
#     """Get the chat history for a specific document"""
#     if document_id not in document_store:
#         raise HTTPException(status_code=404, detail="Document not found")
    
#     history = chat_history_store.get(document_id, [])
    
#     return ChatHistoryResponse(
#         document_id=document_id,
#         history=history
#     )


# @router.delete("/{document_id}/chat/history")
# async def clear_chat_history(
#     document_id: str = Path(..., description="The ID of the document"),
# ):
#     """Clear the chat history for a specific document"""
#     if document_id not in document_store:
#         raise HTTPException(status_code=404, detail="Document not found")
    
#     if document_id in chat_history_store:
#         chat_history_store[document_id] = []
    
#     return {"message": "Chat history cleared successfully"}


# from fastapi import APIRouter, HTTPException, Path, Query
# from pydantic import BaseModel, Field
# from typing import List, Dict, Any, Optional
# import re
# import json
# import os
# from datetime import datetime
# from utils.embedding import DocumentProcessor
# from utils.language_model import LanguageModel
# from routers.documents import document_store

# router = APIRouter()

# language_model = LanguageModel()

# class QueryRequest(BaseModel):
#     question: str = Field(..., description="Question about the document")
#     max_tokens: int = Field(1000, description="Maximum response tokens")
#     top_k: int = Field(4, description="Number of similar chunks to retrieve")

# class QueryResponse(BaseModel):
#     document_id: str
#     question: str
#     answer: str
#     input_tokens: Optional[int] = None
#     output_tokens: Optional[int] = None
#     chunks_used: Optional[int] = None
#     has_table: bool = False
#     table_data: Optional[List[Dict[str, Any]]] = None
#     table_title: Optional[str] = None
#     referenced_pages: Optional[List[int]] = None

# def parse_markdown_table(markdown_text):
#     """Parse markdown tables into structured data."""
#     try:
#         table_lines = markdown_text.strip().split('\n')
#         header = [h.strip() for h in table_lines[0].strip('|').split('|')]
#         rows = []
#         for line in table_lines[2:]:
#             row = [cell.strip() for cell in line.strip('|').split('|')]
#             if len(row) == len(header):
#                 rows.append(dict(zip(header, row)))
#         return rows if rows else None
#     except Exception as e:
#         return None

# def is_schedule_request(message):
#     schedule_keywords = [
#         'schedule', 'table', 'tabular', 'fixture', 'equipment',
#         'door schedule', 'window schedule', 'finish schedule', 'hardware schedule'
#     ]
#     return any(keyword in message.lower() for keyword in schedule_keywords)

# def get_document_processor(document_id: str):
#     if document_id not in document_store:
#         raise HTTPException(status_code=404, detail="Document not found")

#     doc_info = document_store[document_id]
#     if doc_info["status"] != "completed":
#         raise HTTPException(status_code=400, detail=f"Document status: {doc_info['status']}")

#     json_path = doc_info.get("structured_json_path")
#     if not json_path or not os.path.exists(json_path):
#         raise HTTPException(status_code=404, detail="Structured document data missing")

#     try:
#         return DocumentProcessor(json_path)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Document loading error: {e}")

# @router.post("/{document_id}/ask", response_model=QueryResponse)
# async def ask_question(
#     query: QueryRequest,
#     document_id: str = Path(..., description="Document ID"),
# ):
#     doc_processor = get_document_processor(document_id)
#     similar_docs = doc_processor.search_similar_documents(query.question, k=query.top_k)

#     answer_data = language_model.search_and_answer(
#         query.question,
#         similar_docs,
#         max_tokens=query.max_tokens
#     )

#     # Extract referenced pages from metadata
#     referenced_pages = list(set(
#         int(doc.metadata.get("page_number", 0))
#         for doc in similar_docs
#         if "page_number" in doc.metadata
#     ))

#     has_table = is_schedule_request(query.question) and "|" in answer_data["answer"]
#     table_data = parse_markdown_table(answer_data["answer"]) if has_table else None
#     table_title = None

#     if has_table:
#         match = re.search(r"#+\s*(.*?(schedule|table))", answer_data["answer"], re.I)
#         table_title = match.group(1).strip() if match else "Extracted Table"

#     return QueryResponse(
#         document_id=document_id,
#         question=query.question,
#         answer=answer_data["answer"],
#         input_tokens=answer_data.get("input_tokens"),
#         output_tokens=answer_data.get("output_tokens"),
#         chunks_used=len(similar_docs),
#         has_table=has_table,
#         table_data=table_data,
#         table_title=table_title,
#         referenced_pages=referenced_pages or None
#     )

# class ChatHistoryEntry(BaseModel):
#     role: str
#     content: str
#     timestamp: str
#     has_table: Optional[bool] = False
#     table_data: Optional[List[Dict[str, Any]]] = None
#     table_title: Optional[str] = None
#     referenced_pages: Optional[List[int]] = None

# class ChatHistoryResponse(BaseModel):
#     document_id: str
#     history: List[ChatHistoryEntry]

# chat_history_store = {}

# @router.post("/{document_id}/chat", response_model=ChatHistoryEntry)
# async def chat_with_document(
#     query: QueryRequest,
#     document_id: str = Path(..., description="Document ID"),
# ):
#     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#     history = chat_history_store.setdefault(document_id, [])

#     user_entry = ChatHistoryEntry(role="user", content=query.question, timestamp=timestamp)
#     history.append(user_entry)

#     doc_processor = get_document_processor(document_id)
#     similar_docs = doc_processor.search_similar_documents(query.question, k=query.top_k)

#     answer_data = language_model.search_and_answer(
#         query.question,
#         similar_docs,
#         max_tokens=query.max_tokens
#     )

#     referenced_pages = list(set(
#         int(doc.metadata.get("page_number", 0))
#         for doc in similar_docs
#         if "page_number" in doc.metadata
#     ))

#     has_table = is_schedule_request(query.question) and "|" in answer_data["answer"]
#     table_data = parse_markdown_table(answer_data["answer"]) if has_table else None
#     table_title = None

#     if has_table:
#         match = re.search(r"#+\s*(.*?(schedule|table))", answer_data["answer"], re.I)
#         table_title = match.group(1).strip() if match else "Extracted Table"

#     assistant_entry = ChatHistoryEntry(
#         role="assistant",
#         content=answer_data["answer"],
#         timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         has_table=has_table,
#         table_data=table_data,
#         table_title=table_title,
#         referenced_pages=referenced_pages or None
#     )
#     history.append(assistant_entry)

#     return assistant_entry

# @router.get("/{document_id}/chat/history", response_model=ChatHistoryResponse)
# async def get_chat_history(document_id: str = Path(..., description="Document ID")):
#     if document_id not in document_store:
#         raise HTTPException(status_code=404, detail="Document not found")
#     history = chat_history_store.get(document_id, [])
#     return ChatHistoryResponse(document_id=document_id, history=history)

# @router.delete("/{document_id}/chat/history")
# async def clear_chat_history(document_id: str = Path(..., description="Document ID")):
#     if document_id not in document_store:
#         raise HTTPException(status_code=404, detail="Document not found")
#     chat_history_store[document_id] = []
#     return {"message": "Chat history cleared successfully"}

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import re
import json
import os
from datetime import datetime
from utils.embedding import DocumentProcessor
from utils.language_model import LanguageModel
from routers.documents import document_store

router = APIRouter()

language_model = LanguageModel()

class QueryRequest(BaseModel):
    question: str = Field(..., description="Question about the document")
    max_tokens: int = Field(1000, description="Maximum response tokens")
    top_k: int = Field(4, description="Number of similar chunks to retrieve")
    save_to_history: bool = Field(True, description="Whether to save this interaction to chat history")

class QueryResponse(BaseModel):
    document_id: str
    question: str
    answer: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    chunks_used: Optional[int] = None
    has_table: bool = False
    table_data: Optional[List[Dict[str, Any]]] = None
    table_title: Optional[str] = None
    referenced_pages: Optional[List[int]] = None
    timestamp: str

class ChatHistoryEntry(BaseModel):
    role: str
    content: str
    timestamp: str
    has_table: Optional[bool] = False
    table_data: Optional[List[Dict[str, Any]]] = None
    table_title: Optional[str] = None
    referenced_pages: Optional[List[int]] = None

class ChatHistoryResponse(BaseModel):
    document_id: str
    history: List[ChatHistoryEntry]

# Storage for chat history per document
chat_history_store = {}

def parse_markdown_table(markdown_text):
    """Parse markdown tables into structured data."""
    try:
        table_lines = markdown_text.strip().split('\n')
        header = [h.strip() for h in table_lines[0].strip('|').split('|')]
        rows = []
        for line in table_lines[2:]:
            row = [cell.strip() for cell in line.strip('|').split('|')]
            if len(row) == len(header):
                rows.append(dict(zip(header, row)))
        return rows if rows else None
    except Exception as e:
        return None

def is_schedule_request(message):
    schedule_keywords = [
        'schedule', 'table', 'tabular', 'fixture', 'equipment',
        'door schedule', 'window schedule', 'finish schedule', 'hardware schedule'
    ]
    return any(keyword in message.lower() for keyword in schedule_keywords)

def get_document_processor(document_id: str):
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_info = document_store[document_id]
    if doc_info["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Document status: {doc_info['status']}")

    json_path = doc_info.get("structured_json_path")
    if not json_path or not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Structured document data missing")

    try:
        return DocumentProcessor(json_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document loading error: {e}")

@router.post("/{document_id}/query", response_model=QueryResponse)
async def query_document(
    query: QueryRequest,
    document_id: str = Path(..., description="Document ID"),
):
    """
    Unified endpoint for querying documents and managing chat history.
    This combines the previous /ask and /chat endpoints.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Save user question to history if requested
    if query.save_to_history:
        history = chat_history_store.setdefault(document_id, [])
        user_entry = ChatHistoryEntry(
            role="user", 
            content=query.question, 
            timestamp=timestamp
        )
        history.append(user_entry)
    
    # Process the query
    doc_processor = get_document_processor(document_id)
    similar_docs = doc_processor.search_similar_documents(query.question, k=query.top_k)

    answer_data = language_model.search_and_answer(
        query.question,
        similar_docs,
        max_tokens=query.max_tokens
    )

    # Extract referenced pages from metadata
    referenced_pages = list(set(
        int(doc.metadata.get("page_number", 0))
        for doc in similar_docs
        if "page_number" in doc.metadata
    ))

    has_table = is_schedule_request(query.question) and "|" in answer_data["answer"]
    table_data = parse_markdown_table(answer_data["answer"]) if has_table else None
    table_title = None

    if has_table:
        match = re.search(r"#+\s*(.*?(schedule|table))", answer_data["answer"], re.I)
        table_title = match.group(1).strip() if match else "Extracted Table"

    # Create response
    response = QueryResponse(
        document_id=document_id,
        question=query.question,
        answer=answer_data["answer"],
        input_tokens=answer_data.get("input_tokens"),
        output_tokens=answer_data.get("output_tokens"),
        chunks_used=len(similar_docs),
        has_table=has_table,
        table_data=table_data,
        table_title=table_title,
        referenced_pages=referenced_pages or None,
        timestamp=timestamp
    )
    
    # Save assistant response to history if requested
    if query.save_to_history:
        assistant_entry = ChatHistoryEntry(
            role="assistant",
            content=answer_data["answer"],
            timestamp=timestamp,
            has_table=has_table,
            table_data=table_data,
            table_title=table_title,
            referenced_pages=referenced_pages or None
        )
        history = chat_history_store.get(document_id, [])
        history.append(assistant_entry)

    return response

@router.get("/{document_id}/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(document_id: str = Path(..., description="Document ID")):
    """Get the complete chat history for a document"""
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    history = chat_history_store.get(document_id, [])
    return ChatHistoryResponse(document_id=document_id, history=history)

@router.delete("/{document_id}/chat/history")
async def clear_chat_history(document_id: str = Path(..., description="Document ID")):
    """Clear the chat history for a document"""
    if document_id not in document_store:
        raise HTTPException(status_code=404, detail="Document not found")
    chat_history_store[document_id] = []
    return {"message": "Chat history cleared successfully"}