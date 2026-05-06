from __future__ import annotations

import os
import time
from typing import Any

import requests
import streamlit as st


APP_NAME = "Construction Document RAG"


def _get_api_base_url() -> str:
    # Avoid using `st.secrets` directly: it raises FileNotFoundError if no secrets.toml exists.
    env_url = os.getenv("API_BASE_URL")
    if env_url:
        return env_url.rstrip("/")
    return "http://localhost:8000/v1"


API_BASE_URL = _get_api_base_url()

st.set_page_config(page_title=APP_NAME, page_icon="🧠", layout="wide")


def load_css() -> None:
    css_path = os.path.join(os.path.dirname(__file__), "ui", "styles.css")
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


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


def get_chat_history(document_id: str) -> list[dict[str, Any]]:
    payload = api_get(f"/documents/{document_id}/chat/history")
    return payload.get("history", [])


def render_citations_chips(citations: list[dict[str, Any]]) -> None:
    if not citations:
        return
    chips = []
    for c in citations[:8]:
        chips.append(f"<span class='rag-cite-chip'>p.{c.get('page_number')}</span>")
    st.markdown(f"<div class='rag-cite-row'>{''.join(chips)}</div>", unsafe_allow_html=True)


load_css()

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
      <div class="rag-title">{APP_NAME}</div>
      <div class="rag-subtitle">
        Premium document intelligence for architecture & construction: extraction, retrieval, and cited answers.
      </div>
      <div class="rag-pills">
        <span class="rag-pill">Workspace</span>
        <span class="rag-pill">Ingestion</span>
        <span class="rag-pill">Retrieval</span>
        <span class="rag-pill">Citations</span>
      </div>
      <div class="rag-grid">
        <div class="rag-panel">
          <h3>Documents</h3>
          <div class="rag-kpi">{doc_count}</div>
          <div class="rag-hint">Processed files available in your workspace.</div>
        </div>
        <div class="rag-panel">
          <h3>Backend</h3>
          <div class="rag-kpi">{'Connected' if backend_ok else 'Offline'}</div>
          <div class="rag-hint">{API_BASE_URL}</div>
        </div>
        <div class="rag-panel">
          <h3>Workspace</h3>
          <div class="rag-kpi">{'Ready' if backend_ok else 'Start API'}</div>
          <div class="rag-hint">Upload a PDF, wait for ingestion, then query with citations.</div>
        </div>
      </div>
      <div class="rag-credit"><b>Built by Hassan Khan</b></div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Workspace Console")
    st.caption("Connectivity & configuration")
    st.markdown(f"**API Base URL**\n\n`{API_BASE_URL}`")

    if backend_ok:
        st.success("Backend connected")
    else:
        st.warning("Backend offline")
        st.code("uvicorn construction_rag.api.main:app --host 0.0.0.0 --port 8000")
        if st.button("Retry connection", use_container_width=True):
            st.rerun()

    st.markdown("---")
    st.markdown("### Environment")
    st.caption("Set in `.env` (see `README.md`).")
    st.write(f"**OPENAI_API_KEY**: {'OK' if os.getenv('OPENAI_API_KEY') else 'missing'}")
    st.write(f"**ANTHROPIC_API_KEY**: {'OK' if os.getenv('ANTHROPIC_API_KEY') else 'missing'}")
    st.write(f"**LLM_PROVIDER**: `{os.getenv('LLM_PROVIDER', 'anthropic')}`")
    st.write(f"**LLM_MODEL**: `{os.getenv('LLM_MODEL', '')}`")


tab_upload, tab_chat = st.tabs(["Upload & Process", "Chat"])

with tab_upload:
    head_l, head_r = st.columns([2.6, 1])
    with head_l:
        st.markdown("<div class='rag-section-title'>Ingestion</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='rag-section-caption'>Upload a PDF and create a searchable workspace index.</div>",
            unsafe_allow_html=True,
        )
    with head_r:
        if st.button("Refresh documents", use_container_width=True):
            st.rerun()

    col_a, col_b = st.columns([1.35, 1])

    with col_a:
        with st.container(border=True):
            st.markdown("#### Upload PDF")
            st.caption("Supports text PDFs and scanned drawings (OCR when configured).")

            if not backend_ok:
                st.warning("Backend offline. Start the API to enable uploads.")
                st.code("uvicorn construction_rag.api.main:app --host 0.0.0.0 --port 8000")
                uploaded = st.file_uploader("PDF", type=["pdf"], disabled=True)
                st.button("Upload & Process", type="primary", disabled=True)
            else:
                uploaded = st.file_uploader("PDF", type=["pdf"])
                can_upload = uploaded is not None
                if st.button("Upload & Process", type="primary", disabled=not can_upload):
                    with st.status("Ingesting document…", expanded=True) as status:
                        status.update(label="Uploading…", state="running")
                        try:
                            data = api_post(
                                "/documents",
                                files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                            )
                        except requests.HTTPError as exc:
                            body = getattr(exc.response, "text", "") if hasattr(exc, "response") else ""
                            status.update(label="Upload failed", state="error")
                            st.code(body or str(exc))
                            st.info("Set env vars in `.env` and check `README.md`, then restart the backend.")
                            st.stop()

                        doc_id = data["id"]
                        status.update(label="Processing…", state="running")
                        st.caption(f"Document ID: `{doc_id}`")

                        progress = st.progress(0)
                        message = st.empty()
                        while True:
                            s = poll_status(doc_id)
                            progress.progress(int(s.get("progress", 0)))
                            message.info(s.get("message") or s.get("status"))
                            if s.get("status") in {"completed", "failed"}:
                                break
                            time.sleep(1.6)

                        if s.get("status") == "completed":
                            status.update(label="Completed", state="complete")
                            st.success("Document is ready. Open the Chat tab to query it.")
                        else:
                            status.update(label="Failed", state="error")
                            st.error("Processing failed.")
                            st.info("Fix configuration in `.env`, restart backend, then re-upload.")

    with col_b:
        with st.container(border=True):
            st.markdown("#### How it works")
            st.caption("A clean, production-style pipeline.")
            st.markdown(
                """
                1. **Extract** text (PDF text + OCR fallback)
                2. **Chunk** into context windows
                3. **Embed** with OpenAI embeddings
                4. **Index** in FAISS (per document)
                5. **Answer** with citations
                """
            )
            st.markdown("---")
            st.markdown("#### Readiness")
            openai_ok = bool(os.getenv("OPENAI_API_KEY"))
            anthropic_ok = bool(os.getenv("ANTHROPIC_API_KEY"))
            st.write(f"- Embeddings: {'OK' if openai_ok else 'Needs OPENAI_API_KEY'}")
            st.write(f"- LLM: {'OK' if anthropic_ok or openai_ok else 'Set ANTHROPIC_API_KEY or OPENAI_API_KEY'}")
            st.caption("For full setup details, see `README.md`.")


with tab_chat:
    st.markdown("<div class='rag-section-title'>AI Workspace</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='rag-section-caption'>Ask questions and get cited answers, Perplexity-style.</div>",
        unsafe_allow_html=True,
    )

    if not backend_ok:
        with st.container(border=True):
            st.warning("Backend offline. Start the API to enable chat.")
            st.code("uvicorn construction_rag.api.main:app --host 0.0.0.0 --port 8000")
        st.stop()

    docs = list_documents()
    completed = [d for d in docs if d.get("status") == "completed"]
    if not completed:
        with st.container(border=True):
            st.info("No processed documents yet.")
            st.caption("Go to **Upload & Process** to ingest your first PDF.")
        st.stop()

    labels = {f"{d['filename']} · {d['id']}": d for d in completed}
    default_label = st.session_state.get("selected_doc_label", "")
    doc_label = st.selectbox("Active document", [""] + list(labels.keys()), index=0 if default_label not in labels else list(labels.keys()).index(default_label) + 1)
    if not doc_label:
        st.info("Select a document to start a conversation.")
        st.stop()

    st.session_state["selected_doc_label"] = doc_label
    doc = labels[doc_label]

    top_l, top_r = st.columns([2.6, 1])
    with top_l:
        st.caption(f"Document: `{doc['id']}`")
    with top_r:
        if st.button("Clear history", use_container_width=True):
            api_delete(f"/documents/{doc['id']}/chat/history")
            st.rerun()

    history = get_chat_history(doc["id"])
    with st.container(border=True):
        for m in history:
            role = m.get("role", "assistant")
            content = m.get("content", "") or ""
            metadata = m.get("metadata") or {}
            citations = metadata.get("citations") or []

            with st.chat_message("user" if role == "user" else "assistant"):
                st.markdown(content)
                if role != "user":
                    render_citations_chips(citations)

    question = st.chat_input("Ask about the document…")
    if question:
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            placeholder.markdown("Thinking…")
            try:
                resp = api_post(f"/documents/{doc['id']}/query", json={"question": question})
            except requests.HTTPError as exc:
                body = getattr(exc.response, "text", "") if hasattr(exc, "response") else ""
                placeholder.empty()
                st.error("Query failed.")
                st.code(body or str(exc))
                st.info("Set required API keys in `.env`, restart backend, and retry. See `README.md`.")
                st.stop()

            placeholder.markdown(resp.get("answer", "") or "")
            render_citations_chips(resp.get("citations") or [])

        st.rerun()
