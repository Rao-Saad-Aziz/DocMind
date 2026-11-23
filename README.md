# Cortex DocMind

Cortex DocMind aik Retrieval-Augmented Generation (RAG) based AI document assistant hai. Yeh staff ke sawalon ke jawab company ke PDF aur Word documents se nikalta hai, har answer ke saath source document aur page number deta hai, aur user ke role ke mutabik confidential documents ko restrict karta hai.

## Project Pipeline

```text
PDF / DOCX
    |
    v
Document ingestion aur text cleaning
    |
    v
Heading-based chunking
    |
    v
Permission metadata aur local index
    |
    +---------------------------+
    |                           |
    v                           v
BM25 keyword search       Vector embeddings
    |                           |
    +-------------+-------------+
                  |
                  v
Cross-encoder reranking
                  |
                  v
Role-based permission filter
                  |
                  v
LLM answer sirf retrieved passages se
                  |
                  v
Citation + source text
```

## Documentation

### `src/` - Core application logic

| File | Kaam |
|---|---|
| `src/config.py` | Project ki settings rakhta hai: model names, chunk size, overlap, folder paths, roles, aur access levels. |
| `src/ingest.py` | PDF aur DOCX files read karta hai, repeated headers/footers remove karta hai, text ko headings aur size ke hisaab se chunks mein split karta hai. Har chunk ko document, page, department, access level aur allowed roles ke saath tag karta hai. |
| `src/index.py` | Chunks ko sentence-transformer embeddings mein convert karta hai aur local JSON/Numpy files mein save karta hai. Streamlit upload ke liye existing index mein naya document add karne ki functionality bhi deta hai. |
| `src/retrieve.py` | BM25 keyword search, semantic vector search aur cross-encoder reranking provide karta hai. Sab se pehle role ke allowed chunks filter karta hai, is liye unauthorized document chunks retrieval tak nahi pahunchte. |
| `src/answer.py` | Retrieved passages ko Ollama model ko deta hai aur document/page citation ke saath answer generate karta hai. Agar koi source nahi milta ya answer ke paas citation nahi hoti to “not found” response deta hai. |
| `src/evaluate.py` | Dev aur test question splits par Recall@5, MRR, faithfulness aur unanswerable-question refusal score karta hai. |
| `src/__init__.py` | `src` folder ko Python package banata hai. |

### `api/` - REST API

| File | Kaam |
|---|---|
| `api/main.py` | FastAPI application aur `/ask` POST endpoint rakhta hai. User se question aur role leta hai, retrieval aur answer pipeline chalata hai, aur answer ke saath source passages return karta hai. API documentation `/docs` par available hoti hai. |
| `api/demo.py` | Khali placeholder file hai. |

#### `/ask` request example

```json
{
  "question": "How many casual leaves do employees get?",
  "role": "staff"
}
```

### `app/` - Streamlit user interface

| File | Kaam |
|---|---|
| `app/demo.py` | Chat-style web interface chalata hai. Role selector, visible document list, password-protected document upload, highlighted source passages, clear-chat button aur example questions provide karta hai. |

### `data/` - Project data

| Folder/File | Kaam |
|---|---|
| `data/docs/` | Input PDF aur DOCX documents. |
| `data/docs/metadata.json` | Har document ka department aur access level define karta hai. |
| `data/index/chunks.json` | Indexed chunk ka text aur metadata. |
| `data/index/vectors.npy` | Chunks ke 384-dimensional embedding vectors. |
| `data/eval/questions.csv` | Evaluation questions, answer document, answer page, answerable flag aur dev/test split. |
| `data/eval/results_dev.csv` | Development split ke BM25, vector aur reranking scores. |
| `data/eval/runs.jsonl` | Har evaluation run ki settings aur metrics ka repeatable log. |

### `tests/` - Security testing

| File | Kaam |
|---|---|
| `tests/leak_test.py` | Confidential documents par based sawal intern role se poochta hai aur har retrieval mode, answer text aur citations mein leakage check karta hai. |
| `tests/__init__.py` | Tests folder ko Python package banata hai. |

### `notebooks/`

Chunking experiments aur analysis ke liye rakha gaya folder hai. Brief ke mutabik is mein different chunk sizes aur overlap values ke results, observations aur charts honi chahiye.

### Root-level files

| File | Kaam |
|---|---|
| `README.md` | Project overview, setup aur documentation. |
| `requirements.txt` | Python dependencies ki list. |
| `env.example` | Environment variable template. Secret keys ya passwords ko is format mein store karna hai. |
| `.env` | Local environment values aur secrets. Isay GitHub par commit nahi karna. |
| `make_sample_docs.py` | Development aur testing ke liye chhota handbook PDF aur confidential Word file generate karta hai. |

## Roles aur access levels

```text
public       -> intern, staff, hr, admin
internal     -> staff, hr, admin
confidential -> hr, admin
```

Intern role confidential HR document ko search, retrieve ya answer mein receive nahi kar sakta.

## Search modes

### BM25 keyword search

Exact words aur term frequency par based baseline search hai. Yeh evaluation ke liye compare kiya jata hai aur embedding se pehle test hota hai.

### Vector search

`sentence-transformers/all-MiniLM-L6-v2` document chunks aur questions ko normalized vectors mein convert karta hai. Vector similarity se top relevant chunks nikalte hain.

### Vector search + reranking

Pehle vector search se top 20 chunks milte hain. Phir `cross-encoder/ms-marco-MiniLM-L-6-v2` question aur har chunk ka saath mein comparison karta hai aur final top 5 chunks select karta hai.

## Chunk metadata

Har chunk ke saath ye information hoti hai:

- `doc`: Document file name
- `page` / `pages`: Source page number
- `text`: Indexed text
- `department`: Document ka department
- `access`: `public`, `internal` ya `confidential`
- `allowed_roles`: Roles jo document dekh sakte hain

Example:

```json
{
  "doc": "hr_salary_policy.docx",
  "page": 1,
  "text": "The manager salary band is 200,000 to 300,000 PKR...",
  "department": "HR",
  "access": "confidential",
  "allowed_roles": ["hr", "admin"]
}
```

## Setup aur installation

### 1. Virtual environment create karein

```powershell
cd "d:\DPO Internship\Project 1\Docmind"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Environment variables configure karein

```powershell
Copy-Item env.example .env
```

Example local Ollama configuration:

```env
LLM_MODEL=llama3.2
CHUNK_SIZE=200
OVERLAP=30
UPLOAD_PASSWORD=your_password
```

Local Ollama model ke liye Ollama installed aur model downloaded hona chahiye:

```powershell
ollama pull llama3.2
```

## Run commands

### Documents generate ya add karein

```powershell
python make_sample_docs.py
```

### Documents inspect karein

```powershell
python -m src.ingest
```

### Embeddings aur local index banayein

```powershell
python -m src.index
```

### Evaluation run karein

```powershell
python -m src.evaluate dev
python -m src.evaluate test
```

### Permission leak test run karein

```powershell
python -m tests.leak_test
```

### Streamlit app start karein

```powershell
streamlit run app/demo.py
```

### FastAPI start karein

```powershell
uvicorn api.main:app --reload
```

API ke liye browser address:

```text
http://127.0.0.1:8000/docs
```

## Evaluation metrics

| Metric | Meaning |
|---|---|
| Recall@5 | Sahi document aur page top 5 retrieved chunks mein aaye ya nahi. |
| MRR | Sahi result ki average reciprocal rank. |
| Faithfulness | Answer ke har claim ko retrieved passages support karti hain ya nahi. |
| Refusal on unanswerable | Unanswerable questions ke liye system ne sahi “not found” response diya ya nahi. |
| Leak count | Intern ne confidential chunk, answer ya citation receive ki ya nahi. |

Question set ko dev aur test splits mein divide karna chahiye. Dev split par chunking aur retrieval tuning hoti hai; test split sirf final reporting ke liye use hota hai.

## Security behavior

- Search se pehle role ke mutabik unauthorized chunks filter hoti hain.
- Retrieved chunks ke bare text ko LLM ke prompt mein `<passage>` tags ke saath bheja jata hai.
- Passage ke andar instructions ko ignore karne ka instruction prompt mein diya gaya hai.
- Answer ke citation check na hone par system “not found” return karta hai.
- Streamlit chat new role select hone par clear ho jata hai.
- API ka `role` field demo-level hai. Production mein role ko login/token system se verify karna chahiye.

## Known limitations

- MongoDB Atlas Vector Search abhi implement nahi hai; project local `chunks.json` aur `vectors.npy` use karta hai.
- `src/answer.py` me currently Ollama implementation hai. `config.py` ke hosted API settings ka answer implementation ke saath full integration verify nahi hua.
- Scanned PDFs ke textless pages detect hote hain, lekin OCR implementation available nahi.
- Chunking heading detection simple line-based rules use karti hai aur complex layouts ke liye reliable nahi ho sakti.
- Question set brief ke required volume se bahut chhota hai.
- README aur result tables ko real 50+ answerable aur 10+ unanswerable questions ke saath update karna zaroori hai.
- API aur Streamlit ko deployment aur public Hugging Face URL ke saath verify karna baqi hai.

## Brief ke remaining deliverables

- 20–40 real public PDF/DOCX documents
- 50+ answerable aur 10+ unanswerable questions
- Chunking experiments notebook
- Test-split results table
- MongoDB Atlas ya clearly documented local alternative
- Faithfulness aur refusal evaluation
- Streamlit deployment
- FastAPI endpoint verification
- One-page report
- 3-minute demo video
