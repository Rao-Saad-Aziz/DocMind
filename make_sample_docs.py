"""Creates a tiny fake test set so you can try DocMind without a real PDF.
Run from the project root:  python make_sample_docs.py"""
import os, json
import pymupdf, docx

os.makedirs("data/docs", exist_ok=True)
os.makedirs("data/eval", exist_ok=True)

# 1. Public handbook PDF: 3 pages, each with a repeated header and footer
pages = [
    ("1. LEAVE POLICY", "Every employee gets 10 casual leaves and 8 sick leaves per year. "
                        "Unused casual leaves cannot be carried forward to the next year."),
    ("2. RESIGNATION", "The notice period for resignation is 30 days. "
                       "Employees on probation must give 14 days notice."),
    ("3. OVERTIME", "Overtime must be approved by the department head in writing. "
                    "Overtime is paid at twice the hourly rate."),
]
pdf = pymupdf.open()
for n, (title, text) in enumerate(pages, 1):
    p = pdf.new_page()
    p.insert_text((72, 40), "ACME Pvt Ltd - Staff Handbook", fontsize=9)       # header
    p.insert_text((72, 100), title, fontsize=14)
    p.insert_textbox(pymupdf.Rect(72, 120, 520, 300), text, fontsize=11)
    p.insert_text((72, 800), f"Page {n}", fontsize=9)                          # footer
pdf.save("data/docs/sample_handbook.pdf")

# 2. Confidential Word file
d = docx.Document()
d.add_paragraph("SALARY BANDS")
d.add_paragraph("The manager salary band is 200,000 to 300,000 PKR per month.")
d.add_paragraph("Bonus decisions are made by the HR director.")
d.save("data/docs/hr_salary_policy.docx")

# 3. metadata.json (keeps anything already there)
path = "data/docs/metadata.json"
meta = json.load(open(path)) if os.path.exists(path) else {}
meta["sample_handbook.pdf"] = {"department": "HR", "access": "public"}
meta["hr_salary_policy.docx"] = {"department": "HR", "access": "confidential"}
json.dump(meta, open(path, "w"), indent=2)

# 4. Sample questions (added once)
q = "data/eval/questions.csv"
old = open(q).read() if os.path.exists(q) else "question,doc,page,answerable,split\n"
if "sample_handbook.pdf" not in old:
    old = old if old.endswith("\n") else old + "\n"
    open(q, "w").write(old + """How many casual leaves do employees get per year?,sample_handbook.pdf,1,yes,dev
What is the notice period for resignation?,sample_handbook.pdf,2,yes,test
Who approves overtime?,sample_handbook.pdf,3,yes,dev
What is the manager salary band?,hr_salary_policy.docx,1,yes,dev
Who decides bonuses?,hr_salary_policy.docx,1,yes,test
What is the CEO's favourite colour?,,,no,dev
Does the company have an office on Mars?,,,no,test
""")
print("Sample files created. Next: python -m src.ingest")
