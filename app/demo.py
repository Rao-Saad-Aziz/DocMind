"""Streamlit app.  Run: streamlit run app/demo.py"""
import os, re, sys, html, hmac
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from src.config import ROLES, ACCESS, DOCS_DIR
from src.index import add_document, ensure_index
from src.retrieve import search, refresh, visible
from src.answer import answer, NOT_FOUND

st.set_page_config(page_title="Cortex DocMind", page_icon="📄", layout="wide")
st.markdown("""<style>
mark {background:#ffe066; color:#000; padding:0 3px; border-radius:3px}
.block-container {max-width: 900px}
</style>""", unsafe_allow_html=True)

@st.cache_resource(show_spinner="First start: reading documents and building the index...")
def startup():
    ensure_index()


startup()

EXAMPLES = ["How many casual leaves do employees get?",
            "What is the notice period for resignation?",
            "Who approves overtime?"]

# ---------------- sidebar: role, your documents, upload ----------------
with st.sidebar:
    st.title("📄 DocMind")
    role = st.selectbox("Your role", ROLES)
    st.caption("You can read: " + ", ".join(a for a, roles in ACCESS.items() if role in roles))

    docs = {c["doc"]: c["access"] for c in visible(role)[0]}
    st.markdown(f"**Your documents ({len(docs)})**")
    for name, access in sorted(docs.items()):
        st.markdown(f"- {name} `{access}`")

    with st.expander("➕ Upload a document (password needed)"):
        password = os.getenv("UPLOAD_PASSWORD")          # set in .env (or as a secret when deployed)
        if not password:
            st.info("Uploading is switched off. Set UPLOAD_PASSWORD in .env to turn it on.")
        elif not st.session_state.get("can_upload"):
            typed = st.text_input("Password", type="password")
            if typed:
                if hmac.compare_digest(typed.encode(), password.encode()):
                    st.session_state.can_upload = True
                    st.rerun()
                st.error("Wrong password")
        else:
            f = st.file_uploader("PDF or Word file", type=["pdf", "docx"])
            dept = st.text_input("Department", "HR")
            access = st.selectbox("Access level", list(ACCESS))
            if f and st.button("Add document", use_container_width=True):
                os.makedirs(DOCS_DIR, exist_ok=True)
                path = os.path.join(DOCS_DIR, os.path.basename(f.name))
                open(path, "wb").write(f.getvalue())
                with st.spinner("Reading and indexing..."):
                    n, empty = add_document(path, dept, access)
                    refresh()
                st.success(f"Added {n} chunks")
                if empty:
                    st.warning(f"Pages {empty} have no text (scanned?). They were skipped.")
            if st.button("🔒 Lock uploads", use_container_width=True):
                st.session_state.can_upload = False
                st.rerun()

    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []

# A new role starts a fresh chat, so one role's answers are never shown to another.
if st.session_state.get("role") != role:
    st.session_state.update(role=role, messages=[])
messages = st.session_state.messages


def highlight(text, question):
    """Escape the text (it is untrusted), then mark the question's words."""
    text = html.escape(text)
    for w in {w for w in re.findall(r"\w+", question) if len(w) > 3}:
        text = re.sub(rf"(?i)\b({re.escape(w)})\b", r"<mark>\1</mark>", text)
    return text


def render(m):
    if m["role"] == "user":
        st.markdown(m["text"])
    elif m["text"] == NOT_FOUND:
        st.warning(NOT_FOUND)
    else:
        # show [doc, p.N] citations as small badges
        st.markdown(re.sub(r"\[([^\]]+, p\.\d+)\]", r"`📎 \1`", m["text"]))
        st.caption(f"Answer built from {len(m['sources'])} passages")
        for c in m["sources"]:
            with st.expander(f"📎 {c['doc']} · page {c['page']}"):
                st.markdown(highlight(c["text"], m["question"]), unsafe_allow_html=True)


# ---------------- main: chat ----------------
st.title("Cortex DocMind")
st.caption("Ask a question about your documents. Every answer cites the document and page, "
           "and only uses files your role is allowed to open.")

if not messages:
    st.markdown("**Try one of these:**")
    for col, q in zip(st.columns(len(EXAMPLES)), EXAMPLES):
        if col.button(q, use_container_width=True):
            st.session_state.pending = q
            st.rerun()

for m in messages:
    with st.chat_message(m["role"]):
        render(m)

question = st.chat_input("Ask a question...") or st.session_state.pop("pending", None)
if question:
    messages.append({"role": "user", "text": question})
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant"):
        with st.spinner("Searching your documents..."):
            chunks = search(question, role, "rerank", 5)
            try:
                text = answer(question, chunks)
            except Exception as e:
                messages.pop()                         # drop the unanswered question
                st.error(f"Could not get an answer. {e}")
                st.stop()
        reply = {"role": "assistant", "text": text, "question": question,
                 "sources": [] if text == NOT_FOUND else chunks}
        render(reply)
    messages.append(reply)