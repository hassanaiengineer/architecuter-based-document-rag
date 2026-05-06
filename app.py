import os
import streamlit as st
import time
import requests

API_BASE_URL = "http://localhost:8000/api"

# Set page configuration
st.set_page_config(
    page_title="Architecture Document Chatbot",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables
if 'current_document_id' not in st.session_state:
    st.session_state.current_document_id = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Custom CSS
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stApp {
        background-color: #f8f9fa;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .chat-message.user {
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
    }
    .chat-message.assistant {
        background-color: #f1f8e9;
        border-left: 5px solid #8bc34a;
    }
    .chat-message .timestamp {
        font-size: 0.8rem;
        color: #888;
        margin-bottom: 0.5rem;
    }
    .chat-message .content {
        font-size: 1rem;
    }
    .file-info {
        background-color: #fff3e0;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 5px solid #ff9800;
    }
    .sidebar .sidebar-content {
        background-color: #e8eaf6;
    }
</style>
""", unsafe_allow_html=True)

def fetch_documents():
    try:
        response = requests.get(f"{API_BASE_URL}/documents/list")
        if response.status_code == 200:
            return response.json().get("documents", [])
    except requests.exceptions.RequestException:
        st.sidebar.error("Failed to connect to API backend.")
    return []

def load_chat_history(document_id):
    try:
        response = requests.get(f"{API_BASE_URL}/queries/{document_id}/chat/history")
        if response.status_code == 200:
            return response.json().get("history", [])
    except requests.exceptions.RequestException:
        pass
    return []

# Sidebar
with st.sidebar:
    st.title("Architecture Document RAG")
    st.markdown("---")
    
    with st.expander("📝 About This App", expanded=True):
        st.markdown("""
        This application helps you analyze architectural documents and construction plans using:
        
        1. **OCR** - Extract text from PDF documents
        2. **Embeddings** - Create searchable vector representations
        3. **RAG** - Use retrieval-augmented generation to answer your questions
        
        Upload a document and start asking questions about it!
        """)
    
    st.markdown("---")
    st.subheader("Processed Documents")
    
    # Display list of processed files
    documents = fetch_documents()
    if documents:
        for doc in documents:
            if doc['status'] == 'completed':
                if st.button(f"📄 {doc['filename']}", key=f"file_{doc['document_id']}"):
                    st.session_state.current_document_id = doc['document_id']
                    st.session_state.chat_history = load_chat_history(doc['document_id'])
                    st.success(f"Selected: {doc['filename']}")
            else:
                st.markdown(f"📄 {doc['filename']} - *{doc['status']}*")
    else:
        st.info("No documents processed yet. Upload one to get started.")
    
    st.markdown("---")
    st.caption("© 2025 Architecture Document RAG")

# Main content area
st.title("🏛️ Architecture Document RAG System")

# Tabs for upload and chat
tab1, tab2 = st.tabs(["📤 Upload & Process", "💬 Chat"])

# Upload & Process tab
with tab1:
    st.header("Upload Architectural Document")
    
    uploaded_file = st.file_uploader("Choose a PDF file", type=['pdf'])
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        process_button = st.button("Process Document", type="primary", disabled=not uploaded_file)
        
    if process_button and uploaded_file:
        status_container = st.empty()
        try:
            status_container.info("Uploading document to API...")
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            response = requests.post(f"{API_BASE_URL}/documents/upload", files=files)
            
            if response.status_code == 200:
                doc_data = response.json()
                doc_id = doc_data["document_id"]
                st.session_state.current_document_id = doc_id
                
                # Polling for status
                progress_bar = st.progress(0)
                while True:
                    status_response = requests.get(f"{API_BASE_URL}/documents/{doc_id}/status")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        progress_bar.progress(int(status_data["progress"]))
                        status_container.info(status_data["message"])
                        
                        if status_data["status"] == "completed":
                            status_container.success("Document processed successfully!")
                            st.session_state.chat_history = []
                            st.rerun()
                        elif status_data["status"] == "failed":
                            status_container.error(f"Processing failed: {status_data['message']}")
                            break
                        
                    time.sleep(2)
            else:
                status_container.error(f"Upload failed: {response.text}")
        except Exception as e:
            status_container.error(f"Error processing document: {str(e)}")

# Chat tab
with tab2:
    st.header("Chat with your Document")
    
    if not st.session_state.current_document_id:
        st.warning("Please select or upload and process a document first before chatting.")
    else:
        # Get the current document filename
        current_file = None
        for doc in fetch_documents():
            if doc['document_id'] == st.session_state.current_document_id:
                current_file = doc
                break
        
        if current_file:
            # Show file info
            st.markdown(f"""
            <div class="file-info">
                <h3>📄 Current Document: {current_file['filename']}</h3>
                <p>Ask questions about this architectural document</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Display chat history
            for message in st.session_state.chat_history:
                role = message["role"]
                content = message["content"]
                timestamp = message.get("timestamp", "")
                
                st.markdown(f"""
                <div class="chat-message {role}">
                    <div class="timestamp">{timestamp}</div>
                    <div class="content">{content}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Query input
            query = st.text_input("Ask a question about your document:", key="query_input")
            
            if st.button("Send", type="primary") and query:
                # Add temporary user message
                now = time.strftime("%Y-%m-%d %H:%M:%S")
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": query,
                    "timestamp": now
                })
                
                with st.spinner("Searching document..."):
                    try:
                        # Call API
                        payload = {
                            "question": query,
                            "max_tokens": 1000,
                            "top_k": 4,
                            "save_to_history": True
                        }
                        response = requests.post(f"{API_BASE_URL}/queries/{st.session_state.current_document_id}/query", json=payload)
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.session_state.chat_history.append({
                                "role": "assistant",
                                "content": data["answer"],
                                "timestamp": data.get("timestamp", time.strftime("%Y-%m-%d %H:%M:%S"))
                            })
                            st.rerun()
                        else:
                            st.error(f"Error from API: {response.text}")
                    except Exception as e:
                        st.error(f"Error processing query: {str(e)}")
            
            # Clear chat button
            if st.button("Clear Chat History"):
                try:
                    requests.delete(f"{API_BASE_URL}/queries/{st.session_state.current_document_id}/chat/history")
                    st.session_state.chat_history = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to clear history: {str(e)}")
