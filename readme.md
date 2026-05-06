# Architecture Document RAG System 🏛️

A complete Retrieval-Augmented Generation (RAG) system specifically designed for analyzing and querying architectural documents, construction plans, and building specifications.

This system extracts text from PDF blueprints and documents using Google Cloud Vision OCR, creates vector embeddings for semantic search, and uses Anthropic's Claude 3.7 Sonnet to provide highly accurate, context-aware answers to your queries.

## 🌟 Features

*   **PDF Processing:** Handles complex architectural PDFs and extracts text using advanced OCR.
*   **Semantic Search:** Uses FAISS and HuggingFace embeddings (`all-MiniLM-L6-v2`) to find the most relevant document sections.
*   **Architectural Intelligence:** Powered by Claude 3.7 Sonnet with specialized prompt engineering to understand construction terminology, measurements, and spatial relationships.
*   **Decoupled Architecture:** 
    *   **FastAPI Backend:** Robust REST API for document processing, background tasks, and querying.
    *   **Streamlit Frontend:** Intuitive, chat-like UI for interacting with your documents.
*   **Data Persistence:** Uses a lightweight SQLite database to store document metadata and chat histories across sessions.

## 🛠️ Tech Stack

*   **Frontend:** Streamlit
*   **Backend:** FastAPI, Uvicorn
*   **LLM Integration:** LangChain, Anthropic API (Claude)
*   **Vector Database:** FAISS (CPU)
*   **Embeddings:** HuggingFace `sentence-transformers`
*   **OCR:** Google Cloud Vision, `pdf2image`
*   **Database:** SQLite

## 🚀 Setup Instructions

### 1. Prerequisites

*   Python 3.9+
*   Poppler (required for `pdf2image` to convert PDFs to images)
    *   **Ubuntu/Debian:** `sudo apt-get install poppler-utils`
    *   **macOS:** `brew install poppler`
    *   **Windows:** `conda install poppler`

### 2. Clone the Repository

```bash
git clone https://github.com/yourusername/architecture-document-rag.git
cd architecture-document-rag
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration & Credentials

You need two sets of credentials to run this application:

**A. Anthropic API Key (Claude)**
Create a `.env` file in the root directory and add your Anthropic API key:
```env
ANTHROPIC_API_KEY=your_api_key_here
```

**B. Google Cloud Vision Credentials**
1. Set up a Google Cloud Project and enable the Cloud Vision API.
2. Create a Service Account and download the JSON key file.
3. Rename the downloaded JSON file to `google-vision-credentials.json` and place it in the root directory of the project.
*(Note: Ensure you update the `self.google_vision_json_path` variable in `utils/ocr.py` to point to this new filename.)*

## 🏃‍♂️ Running the Application

Because this project uses a decoupled architecture, you need to run both the backend API and the frontend UI.

### 1. Start the FastAPI Backend

Open a terminal and run:
```bash
python main.py
```
*The API will start on `http://localhost:8000`. You can view the API documentation at `http://localhost:8000/docs`.*

### 2. Start the Streamlit Frontend

Open a **new** terminal window and run:
```bash
streamlit run app.py
```
*The UI will open in your default browser at `http://localhost:8501`.*

## 📁 Project Structure

*   `app.py`: Streamlit frontend application.
*   `main.py`: FastAPI backend entry point.
*   `document_rag.db`: SQLite database (auto-generated).
*   `routers/`: API endpoints for documents, queries, and admin stats.
*   `utils/`: Core processing logic:
    *   `database.py`: SQLite connection and queries.
    *   `ocr.py`: PDF conversion and Google Vision OCR.
    *   `embedding.py`: Text chunking and FAISS indexing.
    *   `language_model.py`: Anthropic API integration and markdown formatting.
    *   `prompt.py`: Specialized prompts for architectural analysis.
*   `Uploads/`, `Pages/`, `Structured Text/`, `Embeddings/`: Directories generated during document processing.
