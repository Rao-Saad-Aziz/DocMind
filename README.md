# Cortex DocMind
Company documents se sawal poochho — jawab ke saath (document, page) citation. Jawab na mile to "I couldn't find this in your documents."
Role filter: intern / staff / hr / admin (confidential files intern ko kabhi nahi milti).

Stack: Streamlit + SQLite (BM25 search) + Groq LLM. Deploy: GitHub → Streamlit Community Cloud.

## Streamlit Secrets (Manage app → Settings → Secrets)
```
LLM_API_KEY = "gsk_...apni_nayi_key..."
UPLOAD_PASSWORD = "koi-password"
```
Main file path: `app/demo.py`

## Notes
- Documents `data/docs/` mein rakho (GitHub par) — har start par database mein load hote hain.
- App se upload hui files Streamlit Cloud par reboot ke baad chali jati hain (ephemeral); permanent rakhni hon to GitHub `data/docs` mein daalo.
- `data/docs/metadata.json`: {"file.pdf": {"department": "HR", "access": "public|internal|confidential"}}
- Evaluation: `python app/evaluate.py dev` (data/eval/questions.csv chahiye).
