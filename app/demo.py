"""Cortex DocMind: ask your documents a question. Run: streamlit run app/demo.py"""
import os, re, html, hmac
import streamlit as st
import core

st.set_page_config(page_title="Cortex DocMind", page_icon="📄", layout="wide")
st.markdown("""<style>
mark {background:#ffe066; color:#000; padding:0 3px; border-radius:3px}
.block-container {max-width: 900px}
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="First start: reading the documents...")
def startup():
    core.seed()


startup()
EXAMPLES = ["How many casual leaves do employees get?",
            "What is the notice period for resignation?",
            "Who approves overtime?"]

# ---------------- sidebar ----------------
with st.sidebar:
    st.title("📄 DocMind")
    role = st.selectbox("Your role", core.ROLES)
    st.caption("You can read: " + ", ".join(a for a, r in core.ACCESS.items() if role in r))

    docs = core.visible_docs(role)
    st.markdown(f"**Your documents ({len(docs)})**")
    for d in docs:
        st.markdown(f"- {d['name']} `{d['access']}`")

    with st.expander("➕ Upload a document (password needed)"):
        password = core.get_secret("UPLOAD_PASSWORD")
        if not password:
            st.info("Uploading is switched off. Add UPLOAD_PASSWORD in the app's Secrets to turn it on.")
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
            access = st.selectbox("Access level", list(core.ACCESS))
            if f and st.button("Add document", use_container_width=True):
                os.makedirs(core.DOCS_DIR, exist_ok=True)
                path = os.path.join(core.DOCS_DIR, os.path.basename(f.name))
                open(path, "wb").write(f.getvalue())
                with st.spinner("Reading..."):
                    n, empty = core.add_file(path, dept, access)
                st.success(f"Added {n} chunks")
                if empty:
                    st.warning(f"Pages {empty} have no text (scanned?). They were skipped.")
                st.rerun()
            if st.button("🔒 Lock uploads", use_container_width=True):
                st.session_state.can_upload = False
                st.rerun()

    if st.button("🔧 Check LLM connection", use_container_width=True):
        st.info(core.check_llm())
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []

# A new role starts a fresh chat, so one role's answers are never shown to another.
if st.session_state.get("role") != role:
    st.session_state.update(role=role, messages=[])
messages = st.session_state.messages


def highlight(text, question):
    text = html.escape(text)                                   # document text is untrusted
    for w in {w for w in re.findall(r"\w+", question) if len(w) > 3}:
        text = re.sub(rf"(?i)\b({re.escape(w)})\b", r"<mark>\1</mark>", text)
    return text


def render(m):
    if m["role"] == "user":
        st.markdown(m["text"])
    elif m["text"] == core.NOT_FOUND:
        st.warning(core.NOT_FOUND)
    else:
        st.markdown(re.sub(r"\[([^\]]+, p\.\d+)\]", r"`📎 \1`", m["text"]))
        st.caption(f"Answer built from {len(m['sources'])} passages")
        for c in m["sources"]:
            with st.expander(f"📎 {c['doc']} · page {c['page']}"):
                st.markdown(highlight(c["text"], m["question"]), unsafe_allow_html=True)


# ---------------- chat ----------------
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
            chunks = core.search(question, role)
            try:
                text = core.answer(question, chunks)
            except Exception as e:
                messages.pop()                                # drop the unanswered question
                st.error(f"Could not get an answer. {e}")
                st.stop()
        reply = {"role": "assistant", "text": text, "question": question,
                 "sources": [] if text == core.NOT_FOUND else chunks}
        render(reply)
    messages.append(reply)
