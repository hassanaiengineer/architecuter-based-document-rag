# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# import os
# from routers import documents, queries, admin

# # Create necessary directories
# for directory in ['Uploads', 'Pages', 'Sample Text', 'Structured Text', 'Embeddings']:
#     os.makedirs(directory, exist_ok=True)

# app = FastAPI(
#     title="Architecture Document RAG API",
#     description="API for processing architectural documents and answering questions using RAG",
#     version="1.0.0",
# )

# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Adjust in production
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
# app.include_router(queries.router, prefix="/api/queries", tags=["Queries"])
# app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# @app.get("/")
# async def root():
#     return {"message": "Architecture Document RAG API"}

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from routers import documents, queries, admin

# Create necessary directories if they don't already exist
directories = ['Uploads', 'Pages', 'Sample Text', 'Structured Text', 'Embeddings']
for directory in directories:
    os.makedirs(directory, exist_ok=True)

# Initialize FastAPI application
app = FastAPI(
    title="Architecture Document RAG API",
    description="API for processing architectural documents and answering questions using RAG",
    version="1.0.0",
)

# Configure CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Use "*" to allow all origins, update for production
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods like GET, POST, etc.
    allow_headers=["*"],  # Allow all headers
)

# Include routers for the respective modules
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(queries.router, prefix="/api/queries", tags=["Queries"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Root endpoint to check if the server is running
@app.get("/")
async def root():
    return {"message": "Architecture Document RAG API is up and running!"}

# Main entry point for running the application using uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
