import os
import streamlit as st
import time
import json
from utils.ocr import OCRProcessor
from utils.embedding import DocumentProcessor
from utils.language_model import LanguageModel

# Set page configuration
st.set_page_config(
    page_title="Architecture Document Chatbot",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Create necessary directories
for directory in ['Uploads', 'Pages', 'Sample Text', 'Structured Text', 'Embedding']:
    os.makedirs(directory, exist_ok=True)

# Initialize session state variables
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_json_path' not in st.session_state:
    st.session_state.current_json_path = None
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = []
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# Initialize components
ocr_processor = OCRProcessor()
language_model = LanguageModel()

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
    if st.session_state.processed_files:
        for file_index, file_info in enumerate(st.session_state.processed_files):
            if st.button(f"📄 {file_info['filename']}", key=f"file_{file_index}"):
                st.session_state.current_json_path = file_info['json_path']
                st.session_state.processing_complete = True
                st.success(f"Selected: {file_info['filename']}")
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
        # Display processing status
        status_container = st.empty()
        progress_bar = st.progress(0)
        
        try:
            # Save uploaded file temporarily
            temp_pdf_path = os.path.join("Uploads", uploaded_file.name)
            with open(temp_pdf_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
                
            # Update progress
            status_container.info("PDF saved to uploads folder")
            progress_bar.progress(10)
            time.sleep(0.5)
            
            # Process PDF with OCR
            status_container.info("Running OCR on document...")
            json_path, txt_path = ocr_processor.process_pdf(temp_pdf_path)
            progress_bar.progress(50)
            time.sleep(0.5)
            
            # Generate embeddings
            status_container.info("Creating document embeddings...")
            doc_processor = DocumentProcessor(json_path)
            docs, index = doc_processor.create_faiss_index()
            progress_bar.progress(90)
            time.sleep(0.5)
            
            # Update session state
            file_info = {
                "filename": uploaded_file.name,
                "pdf_path": temp_pdf_path,
                "json_path": json_path,
                "txt_path": txt_path,
                "index_path": doc_processor.index_path,
                "chunks": len(docs)
            }
            
            st.session_state.processed_files.append(file_info)
            st.session_state.current_json_path = json_path
            st.session_state.processing_complete = True
            
            # Complete progress
            progress_bar.progress(100)
            status_container.success("Document processed successfully!")
            
            # Display document info
            with st.expander("Document Processing Details", expanded=True):
                st.markdown(f"**File:** {uploaded_file.name}")
                st.markdown(f"**Total Pages:** {len(json.load(open(json_path)).keys())}")
                st.markdown(f"**Chunks Created:** {len(docs)}")
                st.markdown(f"**Embedding Model:** all-MiniLM-L6-v2")
                
                # Show sample text preview
                with open(txt_path, 'r', encoding='utf-8') as f:
                    sample_text = f.read()[:500] + "..."
                st.text_area("Text Preview:", sample_text, height=200)
            
        except Exception as e:
            status_container.error(f"Error processing document: {str(e)}")
            st.exception(e)

# Chat tab
with tab2:
    st.header("Chat with your Document")
    
    if not st.session_state.processing_complete:
        st.warning("Please upload and process a document first before chatting.")
    else:
        # Get the current document filename
        current_file = None
        for file_info in st.session_state.processed_files:
            if file_info['json_path'] == st.session_state.current_json_path:
                current_file = file_info
                break
        
        if current_file:
            # Show file info
            st.markdown(f"""
            <div class="file-info">
                <h3>📄 Current Document: {current_file['filename']}</h3>
                <p>Ask questions about this architectural document</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Chat interface
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
                # Add user message to chat history
                now = time.strftime("%H:%M:%S")
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": query,
                    "timestamp": now
                })
                
                # Display user message immediately
                st.markdown(f"""
                <div class="chat-message user">
                    <div class="timestamp">{now}</div>
                    <div class="content">{query}</div>
                </div>
                """, unsafe_allow_html=True)
                
                # Process query
                try:
                    with st.spinner("Searching document..."):
                        # Create document processor if needed
                        doc_processor = DocumentProcessor(st.session_state.current_json_path)
                        
                        # Retrieve similar documents
                        similar_docs = doc_processor.search_similar_documents(query)
                        
                        # Generate answer
                        answer = language_model.search_and_answer(query, similar_docs)
                        
                        # Add assistant message to chat history
                        now = time.strftime("%H:%M:%S")
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": answer,
                            "timestamp": now
                        })
                        
                        # Display assistant message
                        st.markdown(f"""
                        <div class="chat-message assistant">
                            <div class="timestamp">{now}</div>
                            <div class="content">{answer}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    st.error(f"Error processing query: {str(e)}")
            
            # Clear chat button
            if st.button("Clear Chat History"):
                st.session_state.chat_history = []
                st.experimental_rerun()