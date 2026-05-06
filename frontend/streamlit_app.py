from __future__ import annotations

import os
import time

import requests
import streamlit as st


def _get_api_base_url() -> str:
    # Avoid using `st.secrets` directly: it raises FileNotFoundError if no secrets.toml exists.
    env_url = os.getenv("API_BASE_URL")
    if env_url:
        return env_url.rstrip("/")
    return "http://localhost:8000/v1"


API_BASE_URL = _get_api_base_url()

st.set_page_config(page_title="Construction Document RAG", layout="wide")


def api_get(path: str):
    resp = requests.get(f"{API_BASE_URL}{path}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def api_post(path: str, **kwargs):
    resp = requests.post(f"{API_BASE_URL}{path}", timeout=120, **kwargs)
    resp.raise_for_status()
    return resp.json()


def api_delete(path: str):
    resp = requests.delete(f"{API_BASE_URL}{path}", timeout=30)
    resp.raise_for_status()
    return resp.json()


def list_documents():
    return api_get("/documents").get("documents", [])


def poll_status(doc_id: str):
    return api_get(f"/documents/{doc_id}/status")


def backend_health() -> bool:
    try:
        return api_get("/admin/health").get("status") == "ok"
    except Exception:
        return False


st.markdown(
    """
    <style>
      :root {
        --rag-border: rgba(148,163,184,0.14);
        --rag-card: rgba(15,23,42,0.52);
        --rag-card-2: rgba(15,23,42,0.34);
        --rag-text: rgba(226,232,240,0.92);
        --rag-muted: rgba(226,232,240,0.72);
        --rag-accent: rgba(124,58,237,0.35);
        --rag-accent-2: rgba(16,185,129,0.22);
      }

      html, body, [class*="css"]  { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, "Noto Sans", "Liberation Sans", sans-serif; }

      .block-container { padding-top: 1.25rem; padding-bottom: 2rem; }
      section[data-testid="stSidebar"] { border-right: 1px solid var(--rag-border); }

      #MainMenu, footer { visibility: hidden; }

      .rag-shell {
        background:
          radial-gradient(900px 400px at 10% 0%, rgba(124,58,237,0.18), transparent 60%),
          radial-gradient(900px 400px at 90% 0%, rgba(16,185,129,0.14), transparent 60%);
        border: 1px solid var(--rag-border);
        border-radius: 16px;
        padding: 1.25rem 1.25rem;
        margin-bottom: 1rem;
      }

      .rag-title {
        margin: 0;
        font-size: 1.55rem;
        font-weight: 650;
        letter-spacing: -0.02em;
      }
      .rag-subtitle { margin: 0.35rem 0 0; color: var(--rag-muted); font-size: 0.98rem; }

      .rag-pills { margin-top: 0.85rem; display: flex; gap: 0.45rem; flex-wrap: wrap; }
      .rag-pill {
        padding: 0.22rem 0.55rem;
        border-radius: 999px;
        font-size: 0.82rem;
        border: 1px solid var(--rag-border);
        background: rgba(2,6,23,0.20);
        color: var(--rag-text);
        backdrop-filter: blur(10px);
      }

      .rag-grid { display: grid; grid-template-columns: 1.4fr 1fr; gap: 0.9rem; align-items: stretch; margin-top: 0.9rem; }
      .rag-panel {
        border: 1px solid var(--rag-border);
        border-radius: 14px;
        background: var(--rag-card);
        padding: 0.95rem 1rem;
      }
      .rag-panel h3 { margin: 0; font-size: 0.9rem; font-weight: 650; color: var(--rag-muted); text-transform: uppercase; letter-spacing: .06em; }
      .rag-panel .kpi { margin-top: 0.4rem; font-size: 1.15rem; font-weight: 650; }
      .rag-panel .hint { margin-top: 0.35rem; color: var(--rag-muted); font-size: 0.9rem; }

      .rag-credit { margin-top: 0.75rem; color: var(--rag-text); font-size: 0.95rem; }
      .rag-credit b { font-weight: 650; }

      .rag-card {
        border: 1px solid var(--rag-border);
        border-radius: 14px;
        padding: 0.95rem 1rem;
        background: var(--rag-card-2);
      }

      /* Make default Streamlit headers less heavy */
      h2, h3 { font-weight: 650 !important; letter-spacing: -0.01em; }
      h2 { font-size: 1.15rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

backend_ok = backend_health()
doc_count = 0
if backend_ok:
    try:
        doc_count = len(list_documents())
    except Exception:
        doc_count = 0

st.markdown(
    f"""
    <div class="rag-shell">
      <div>
        <div class="rag-title">Construction Document RAG</div>
        <div class="rag-subtitle">Document intelligence for construction/architecture: extraction, retrieval, and cited answers.</div>
        <div class="rag-pills">
          <span class="rag-pill">FastAPI</span>
          <span class="rag-pill">FAISS</span>
          <span class="rag-pill">OCR</span>
          <span class="rag-pill">Citations</span>
        </div>
        <div class="rag-grid">
          <div class="rag-panel">
            <h3>Workspace</h3>
            <div class="kpi">{doc_count} documents</div>
            <div class="hint">Upload a PDF, wait for ingestion, then query with citations.</div>
          </div>
          <div class="rag-panel">
            <h3>Backend</h3>
            <div class="kpi">{'Connected' if backend_ok else 'Offline'}</div>
            <div class="hint">{API_BASE_URL}</div>
          </div>
        </div>
        <div class="rag-credit"><b>Built by Hassan Khan</b></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Console")
    st.caption("Workspace connectivity & configuration")
    st.markdown(f"**API Base URL**\n\n`{API_BASE_URL}`")
    st.markdown("---")
    if backend_ok:
        st.success("Backend connected")
    else:
        st.warning("Backend offline")
        st.code("uvicorn construction_rag.api.main:app --host 0.0.0.0 --port 8000")

    st.markdown("---")
    st.markdown("### Environment")
    st.caption("Set in `.env` (see `README.md`).")
    st.write(f"**OPENAI_API_KEY**: {'OK' if os.getenv('OPENAI_API_KEY') else 'missing'}")
    st.write(f"**ANTHROPIC_API_KEY**: {'OK' if os.getenv('ANTHROPIC_API_KEY') else 'missing'}")
    st.write(f"**LLM_PROVIDER**: `{os.getenv('LLM_PROVIDER', 'anthropic')}`")
    st.write(f"**LLM_MODEL**: `{os.getenv('LLM_MODEL', '')}`")


tab_upload, tab_chat = st.tabs(["Upload & Process", "Chat"])

with tab_upload:
    st.subheader("Upload")
    st.caption("Ingest a PDF into your workspace index.")
    st.markdown('<div class="rag-card">Tip: scanned drawings benefit from OCR. Text-based PDFs ingest faster.</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader("PDF", type=["pdf"])

    can_upload = backend_ok and uploaded is not None
    if st.button("Upload & Process", type="primary", disabled=not can_upload, use_container_width=False):
        if not backend_ok:
            st.warning("Backend is not connected. Start the API and try again.")
            st.stop()

        with st.spinner("Uploading..."):
            try:
                data = api_post(
                    "/documents",
                    files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                )
            except requests.HTTPError as exc:
                body = getattr(exc.response, "text", "") if hasattr(exc, "response") else ""
                st.error("Upload failed.")
                st.code(body or str(exc))
                st.info("Fix configuration in `.env` and check `README.md`, then restart the backend.")
                st.stop()

        doc_id = data["id"]
        st.success(f"Uploaded: {uploaded.name}")
        st.caption(f"Document ID: `{doc_id}`")

        progress = st.progress(0)
        status_box = st.empty()
        while True:
            status = poll_status(doc_id)
            progress.progress(int(status["progress"]))
            status_box.info(f"{status['status']}: {status.get('message') or ''}")
            if status["status"] in {"completed", "failed"}:
                break
            time.sleep(2)

        if status["status"] == "failed":
            st.error("Processing failed.")
            st.info("Set the required env vars in `.env`, restart the backend, and re-upload.")


with tab_chat:
    st.subheader("Chat")
    st.caption("Query a processed document and get cited answers.")

    if not backend_ok:
        st.info("Backend is not connected. Start the API to list documents and query.")
        st.stop()

    docs = list_documents()
    options = {f"{d['filename']} ({d['status']}) - {d['id']}": d for d in docs}
    selected_key = st.selectbox("Document", [""] + list(options.keys()))

    if not selected_key:
        st.info("Select a processed document to start chatting.")
        st.stop()

    doc = options[selected_key]
    if doc["status"] != "completed":
        st.warning("Document is not processed yet.")
        st.stop()

    q = st.text_input("Question", placeholder="e.g., What is the slab thickness and where is it specified?")
    if st.button("Ask", type="primary", disabled=not q.strip()):
        with st.spinner("Retrieving & generating answer..."):
            try:
                resp = api_post(f"/documents/{doc['id']}/query", json={"question": q})
            except requests.HTTPError as exc:
                body = getattr(exc.response, "text", "") if hasattr(exc, "response") else ""
                st.error("Query failed.")
                st.code(body or str(exc))
                st.info("Set required API keys in `.env`, restart backend, and retry. See `README.md`.")
                st.stop()

        st.markdown(resp.get("answer", "") or "")
        with st.expander("Citations"):
            for c in resp.get("citations", []):
                st.markdown(f"- p.{c['page_number']} (`{c['chunk_id']}`): {c['excerpt']}")

    col_a, col_b = st.columns([1, 3])
    with col_a:
        if st.button("Clear chat history"):
            api_delete(f"/documents/{doc['id']}/chat/history")
            st.success("Cleared.")
