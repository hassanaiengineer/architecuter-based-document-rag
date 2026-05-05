# from fastapi import APIRouter, HTTPException, Path, Query, Depends, BackgroundTasks
# from pydantic import BaseModel
# from typing import List, Dict, Any, Optional
# import os
# import shutil
# import json
# import time
# import logging
# import psutil
# from routers.documents import document_store
# from routers.queries import chat_history_store

# router = APIRouter()

# logger = logging.getLogger(__name__)


# class SystemStats(BaseModel):
#     cpu_percent: float
#     memory_percent: float
#     disk_usage_percent: float
#     processed_documents: int
#     pending_documents: int
#     failed_documents: int


# class DocumentStats(BaseModel):
#     total_documents: int
#     total_pages: int
#     total_chunks: int
#     average_chunks_per_page: float
#     document_statuses: Dict[str, int]


# class DocumentDirectoryStats(BaseModel):
#     uploads_dir_size_mb: float
#     pages_dir_size_mb: float
#     text_dir_size_mb: float
#     json_dir_size_mb: float
#     embeddings_dir_size_mb: float


# def get_dir_size(path):
#     """Get directory size in bytes"""
#     total_size = 0
#     if os.path.exists(path):
#         for dirpath, dirnames, filenames in os.walk(path):
#             for f in filenames:
#                 fp = os.path.join(dirpath, f)
#                 total_size += os.path.getsize(fp)
#     return total_size


# @router.get("/stats/system", response_model=SystemStats)
# async def get_system_stats():
#     """Get system statistics"""
#     try:
#         # Get document counts by status
#         processed_docs = sum(1 for doc in document_store.values() if doc["status"] == "completed")
#         pending_docs = sum(1 for doc in document_store.values() if doc["status"] in ["pending", "processing"])
#         failed_docs = sum(1 for doc in document_store.values() if doc["status"] == "failed")
        
#         return SystemStats(
#             cpu_percent=psutil.cpu_percent(),
#             memory_percent=psutil.virtual_memory().percent,
#             disk_usage_percent=psutil.disk_usage('/').percent,
#             processed_documents=processed_docs,
#             pending_documents=pending_docs,
#             failed_documents=failed_docs
#         )
#     except Exception as e:
#         logger.error(f"Error getting system stats: {e}")
#         raise HTTPException(status_code=500, detail=f"Error getting system stats: {str(e)}")


# @router.get("/stats/documents", response_model=DocumentStats)
# async def get_document_stats():
#     """Get document statistics"""
#     try:
#         # Count documents by status
#         status_counts = {}
#         total_pages = 0
#         total_chunks = 0
        
#         for doc in document_store.values():
#             status = doc["status"]
#             status_counts[status] = status_counts.get(status, 0) + 1
            
#             # Sum up pages and chunks for completed documents
#             if status == "completed":
#                 total_pages += doc.get("pages", 0)
#                 total_chunks += doc.get("chunks", 0)
        
#         # Calculate average chunks per page
#         avg_chunks_per_page = 0
#         if total_pages > 0:
#             avg_chunks_per_page = total_chunks / total_pages
        
#         return DocumentStats(
#             total_documents=len(document_store),
#             total_pages=total_pages,
#             total_chunks=total_chunks,
#             average_chunks_per_page=avg_chunks_per_page,
#             document_statuses=status_counts
#         )
#     except Exception as e:
#         logger.error(f"Error getting document stats: {e}")
#         raise HTTPException(status_code=500, detail=f"Error getting document stats: {str(e)}")


# @router.get("/stats/storage", response_model=DocumentDirectoryStats)
# async def get_storage_stats():
#     """Get storage statistics for document directories"""
#     try:
#         # Calculate directory sizes in MB
#         uploads_size = get_dir_size("Uploads") / (1024 * 1024)
#         pages_size = get_dir_size("Pages") / (1024 * 1024)
#         text_size = get_dir_size("Sample Text") / (1024 * 1024)
#         json_size = get_dir_size("Structured Text") / (1024 * 1024)
#         embeddings_size = get_dir_size("Embeddings") / (1024 * 1024)
        
#         return DocumentDirectoryStats(
#             uploads_dir_size_mb=uploads_size,
#             pages_dir_size_mb=pages_size,
#             text_dir_size_mb=text_size,
#             json_dir_size_mb=json_size,
#             embeddings_dir_size_mb=embeddings_size
#         )
#     except Exception as e:
#         logger.error(f"Error getting storage stats: {e}")
#         raise HTTPException(status_code=500, detail=f"Error getting storage stats: {str(e)}")


# @router.post("/cleanup", status_code=202)
# async def cleanup_temp_files(background_tasks: BackgroundTasks):
#     """Clean up temporary files like extracted images"""
    
#     def cleanup_task():
#         try:
#             # Keep track of files we want to preserve
#             preserved_files = set()
            
#             # Collect files we need to preserve from document store
#             for doc in document_store.values():
#                 if "file_path" in doc:
#                     preserved_files.add(doc["file_path"])
#                 if "structured_json_path" in doc:
#                     preserved_files.add(doc["structured_json_path"])
#                 if "text_path" in doc:
#                     preserved_files.add(doc["text_path"])
            
#             # Clean up Pages directory (contains extracted images)
#             pages_dir = "Pages"
#             if os.path.exists(pages_dir):
#                 for filename in os.listdir(pages_dir):
#                     file_path = os.path.join(pages_dir, filename)
#                     if file_path not in preserved_files:
#                         if os.path.isfile(file_path):
#                             os.remove(file_path)
#                             logger.info(f"Removed temporary file: {file_path}")
            
#             logger.info("Cleanup task completed")
            
#         except Exception as e:
#             logger.error(f"Error in cleanup task: {e}")
    
#     # Run the cleanup task in the background
#     background_tasks.add_task(cleanup_task)
    
#     return {"message": "Cleanup task started"}


# @router.delete("/reset", status_code=202)
# async def reset_application(background_tasks: BackgroundTasks):
#     """Reset the application to its initial state (clear all data)"""
    
#     def reset_task():
#         try:
#             # Clear all document data
#             document_store.clear()
#             chat_history_store.clear()
            
#             # Remove all files in the directories
#             directories = ['Uploads', 'Pages', 'Sample Text', 'Structured Text', 'Embeddings']
            
#             for directory in directories:
#                 if os.path.exists(directory):
#                     for item in os.listdir(directory):
#                         item_path = os.path.join(directory, item)
#                         if os.path.isfile(item_path):
#                             os.remove(item_path)
#                         elif os.path.isdir(item_path):
#                             shutil.rmtree(item_path)
            
#             logger.info("Application reset completed")
            
#         except Exception as e:
#             logger.error(f"Error in reset task: {e}")
    
#     # Run the reset task in the background
#     background_tasks.add_task(reset_task)
    
#     return {"message": "Reset task started"}

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict
import os
import shutil
import logging
import psutil
from routers.documents import document_store
from routers.queries import chat_history_store

router = APIRouter()
logger = logging.getLogger(__name__)

class SystemStats(BaseModel):
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    processed_documents: int
    pending_documents: int
    failed_documents: int

class DocumentStats(BaseModel):
    total_documents: int
    total_pages: int
    total_chunks: int
    average_chunks_per_page: float
    document_statuses: Dict[str, int]

class DocumentDirectoryStats(BaseModel):
    uploads_dir_size_mb: float
    pages_dir_size_mb: float
    text_dir_size_mb: float
    json_dir_size_mb: float
    embeddings_dir_size_mb: float

def get_dir_size(path):
    """Calculate directory size in bytes."""
    total_size = 0
    abs_path = os.path.abspath(path)
    if os.path.exists(abs_path):
        for dirpath, dirnames, filenames in os.walk(abs_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
    return total_size

@router.get("/stats/system", response_model=SystemStats)
async def get_system_stats():
    """Get current system statistics."""
    try:
        processed_docs = sum(1 for doc in document_store.values() if doc["status"] == "completed")
        pending_docs = sum(1 for doc in document_store.values() if doc["status"] in ["pending", "processing"])
        failed_docs = sum(1 for doc in document_store.values() if doc["status"] == "failed")

        return SystemStats(
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage('/').percent,
            processed_documents=processed_docs,
            pending_documents=pending_docs,
            failed_documents=failed_docs
        )
    except Exception as e:
        logger.error(f"System stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/documents", response_model=DocumentStats)
async def get_document_stats():
    """Get document processing statistics."""
    try:
        status_counts = {}
        total_pages = 0
        total_chunks = 0

        for doc in document_store.values():
            status = doc["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
            if status == "completed":
                total_pages += doc.get("pages", 0)
                total_chunks += doc.get("chunks", 0)

        avg_chunks_per_page = (total_chunks / total_pages) if total_pages else 0

        return DocumentStats(
            total_documents=len(document_store),
            total_pages=total_pages,
            total_chunks=total_chunks,
            average_chunks_per_page=avg_chunks_per_page,
            document_statuses=status_counts
        )
    except Exception as e:
        logger.error(f"Document stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/storage", response_model=DocumentDirectoryStats)
async def get_storage_stats():
    """Get storage statistics for directories."""
    try:
        dirs = ["Uploads", "Pages", "Sample Text", "Structured Text", "Embeddings"]
        sizes = [get_dir_size(d) / (1024 * 1024) for d in dirs]

        return DocumentDirectoryStats(
            uploads_dir_size_mb=sizes[0],
            pages_dir_size_mb=sizes[1],
            text_dir_size_mb=sizes[2],
            json_dir_size_mb=sizes[3],
            embeddings_dir_size_mb=sizes[4]
        )
    except Exception as e:
        logger.error(f"Storage stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup", status_code=202)
async def cleanup_temp_files(background_tasks: BackgroundTasks):
    """Initiate cleanup of temporary files."""

    def cleanup_task():
        preserved_files = {
            os.path.abspath(doc[key])
            for doc in document_store.values()
            for key in ["file_path", "structured_json_path", "text_path"]
            if key in doc
        }

        pages_dir = os.path.abspath("Pages")
        if os.path.exists(pages_dir):
            for filename in os.listdir(pages_dir):
                file_path = os.path.abspath(os.path.join(pages_dir, filename))
                if file_path not in preserved_files and os.path.isfile(file_path):
                    os.remove(file_path)
                    logger.info(f"Removed temporary file: {file_path}")

        logger.info("Cleanup completed successfully.")

    background_tasks.add_task(cleanup_task)
    return {"message": "Cleanup task initiated."}

@router.delete("/reset", status_code=202)
async def reset_application(background_tasks: BackgroundTasks):
    """Reset application by clearing all stored data."""

    def reset_task():
        document_store.clear()
        chat_history_store.clear()

        for directory in ['Uploads', 'Pages', 'Sample Text', 'Structured Text', 'Embeddings']:
            abs_directory = os.path.abspath(directory)
            if os.path.exists(abs_directory):
                for item in os.listdir(abs_directory):
                    item_path = os.path.join(abs_directory, item)
                    try:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        logger.info(f"Deleted: {item_path}")
                    except Exception as e:
                        logger.error(f"Error deleting {item_path}: {e}")

        logger.info("Application reset completed successfully.")

    background_tasks.add_task(reset_task)
    return {"message": "Reset task initiated."}
