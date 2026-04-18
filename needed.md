# FairLens — Complete Installation Guide

Run every command in order. Copy-paste friendly.

---

## SYSTEM REQUIREMENTS

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Git

---

## STEP 1 — Install System Dependencies

### Mac
```bash
brew install python@3.11 node postgresql redis
brew services start postgresql
brew services start redis
```

### Ubuntu / Debian
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip nodejs npm \
                    postgresql postgresql-contrib redis-server \
                    libpq-dev build-essential libxml2-dev libxslt-dev \
                    libffi-dev libcairo2 libpango-1.0-0 libpangocairo-1.0-0 \
                    libgdk-pixbuf2.0-0 libglib2.0-dev
sudo systemctl start postgresql
sudo systemctl start redis
```

### Windows
```
1. Install Python 3.11 from https://python.org
2. Install Node.js 18 from https://nodejs.org
3. Install PostgreSQL from https://postgresql.org/download/windows
4. Install Redis from https://github.com/microsoftarchive/redis/releases
   OR use WSL2 (recommended) and follow Ubuntu steps above
```

---

## STEP 2 — Clone & Create Project Structure

```bash
mkdir fairlens && cd fairlens
mkdir -p backend/routers backend/services backend/templates backend/reg_docs
mkdir -p frontend
git init
```

---

## STEP 3 — Backend: Python Virtual Environment

```bash
cd backend
python3.11 -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

---

## STEP 4 — Backend: Install All Python Packages

```bash
# Core framework
pip install fastapi==0.111.0
pip install uvicorn[standard]==0.29.0
pip install python-multipart==0.0.9
pip install python-dotenv==1.0.1
pip install pydantic==2.7.1

# Data
pip install pandas==2.2.2
pip install numpy==1.26.4
pip install pyarrow==16.1.0

# Dataset profiling
pip install ydata-profiling==4.8.3

# ML + Fairness
pip install scikit-learn==1.4.2
pip install fairlearn==0.10.0
pip install aif360==0.6.1
pip install imbalanced-learn==0.12.2
pip install scipy==1.13.0

# Explainability
pip install shap==0.45.0
pip install onnxruntime==1.18.0

# LLM + AI
pip install anthropic==0.25.0

# RAG / Vector DB
pip install chromadb==0.5.0
pip install sentence-transformers==2.7.0

# PDF parsing (for regulation docs)
pip install PyPDF2==3.0.1

# PDF generation
pip install weasyprint==62.3
pip install jinja2==3.1.4

# Database
pip install sqlalchemy==2.0.30
pip install psycopg2-binary==2.9.9

# Cache
pip install redis==5.0.4

# Utilities
pip install httpx==0.27.0
pip install python-jose==3.3.0
pip install passlib==1.7.4
```

### Or install everything at once from requirements.txt:

```bash
# Save this as backend/requirements.txt first, then:
pip install -r requirements.txt
```

```
# backend/requirements.txt
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
python-dotenv==1.0.1
pydantic==2.7.1
pandas==2.2.2
numpy==1.26.4
pyarrow==16.1.0
ydata-profiling==4.8.3
scikit-learn==1.4.2
fairlearn==0.10.0
aif360==0.6.1
imbalanced-learn==0.12.2
scipy==1.13.0
shap==0.45.0
onnxruntime==1.18.0
anthropic==0.25.0
chromadb==0.5.0
sentence-transformers==2.7.0
PyPDF2==3.0.1
weasyprint==62.3
jinja2==3.1.4
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
redis==5.0.4
httpx==0.27.0
```

---

## STEP 5 — Backend: Environment Variables

```bash
# Create backend/.env
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-your-key-here
DATABASE_URL=postgresql://fairlens:password@localhost:5432/fairlens
REDIS_URL=redis://localhost:6379
STORAGE_PATH=/tmp/fairlens_datasets
EOF
```

Get your Anthropic API key at: https://console.anthropic.com

---

## STEP 6 — Database Setup

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE USER fairlens WITH PASSWORD 'password';"
psql -U postgres -c "CREATE DATABASE fairlens OWNER fairlens;"
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE fairlens TO fairlens;"

# Verify connection
psql postgresql://fairlens:password@localhost:5432/fairlens -c "\l"
```

---

## STEP 7 — Frontend: Install Node Packages

```bash
# From project root
cd ../frontend

# Create Next.js app (if not already done)
npx create-next-app@latest . --typescript --tailwind --app --no-git --yes

# Install additional packages
npm install axios
npm install react-dropzone
npm install recharts
npm install @radix-ui/react-tabs
npm install @radix-ui/react-dialog
npm install lucide-react
npm install clsx
npm install tailwind-merge
```

---

## STEP 8 — Frontend: Environment Variables

```bash
# Create frontend/.env.local
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000
EOF
```

---

## STEP 9 — Download Demo Datasets

```bash
# From backend directory (with venv activated)
cd ../backend

python3 - << 'EOF'
import pandas as pd
import os

os.makedirs("/tmp/fairlens_datasets", exist_ok=True)

# COMPAS Recidivism dataset
print("Downloading COMPAS dataset...")
url = "https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv"
df = pd.read_csv(url)
df = df[['age','sex','race','priors_count','decile_score','two_year_recid']].dropna()
df['prediction'] = (df['decile_score'] >= 5).astype(int)
df.to_parquet("/tmp/fairlens_datasets/demo_compas.parquet")
df.to_csv("/tmp/fairlens_datasets/demo_compas.csv", index=False)
print(f"COMPAS: {len(df)} rows saved")

# German Credit via AIF360
print("Downloading German Credit dataset...")
from aif360.datasets import GermanDataset
gd = GermanDataset()
df2, _ = gd.convert_to_dataframe()
df2.to_parquet("/tmp/fairlens_datasets/demo_german.parquet")
df2.to_csv("/tmp/fairlens_datasets/demo_german.csv", index=False)
print(f"German Credit: {len(df2)} rows saved")

print("Demo datasets ready!")
EOF
```

---

## STEP 10 — Build RAG Index (Regulation Docs)

```bash
# Download free regulation PDFs
# Place them in backend/reg_docs/
# Minimum needed for demo:

# Option A: Use placeholder text files if PDFs unavailable
python3 - << 'EOF'
import os
os.makedirs("reg_docs", exist_ok=True)

# Create minimal regulation text files for demo
regs = {
    "eeoc.txt": """EEOC Uniform Guidelines on Employee Selection Procedures.
Section 1607.4(D) Adverse Impact. A selection rate for any race, sex, or ethnic group 
which is less than four-fifths (4/5) (or eighty percent) of the rate for the group 
with the highest rate will generally be regarded by the Federal enforcement agencies 
as evidence of adverse impact. This is known as the 4/5ths rule or 80% rule.
Employers must be able to demonstrate that any selection procedure that has adverse 
impact is job-related and consistent with business necessity.""",

    "gdpr_art22.txt": """GDPR Article 22 - Automated individual decision-making, including profiling.
The data subject shall have the right not to be subject to a decision based solely on 
automated processing, including profiling, which produces legal effects concerning him 
or her or similarly significantly affects him or her.
Member States may provide that point (a) of paragraph 2 shall not apply to decisions 
referred to in that paragraph if the decision is necessary for entering into, or 
performance of, a contract between the data subject and a data controller.""",

    "eu_ai_act.txt": """EU AI Act Title III - High-Risk AI Systems.
Article 10: Data and data governance. Training, validation and testing data sets shall 
be subject to appropriate data governance and management practices. Training, validation 
and testing data sets shall be relevant, sufficiently representative, and to the best 
extent possible, free of errors and complete in view of the intended purpose.
They shall have the appropriate statistical properties, including, where applicable, 
as regards the persons or groups of persons on which the high-risk AI system is 
intended to be used, with specific attention to the possible biases that could 
affect health and safety or lead to discrimination prohibited by Union law.""",

    "uk_equality.txt": """UK Equality Act 2010.
Section 4: Protected characteristics include age, disability, gender reassignment, 
marriage and civil partnership, pregnancy and maternity, race, religion or belief, 
sex, and sexual orientation.
Section 19: Indirect discrimination. A person (A) discriminates against another (B) 
if A applies to B a provision, criterion or practice which is discriminatory in 
relation to a relevant protected characteristic of B's."""
}

for filename, content in regs.items():
    with open(f"reg_docs/{filename}", 'w') as f:
        f.write(content)
    print(f"Created: reg_docs/{filename}")

print("Regulation docs ready!")
EOF
```

```python
# backend/build_rag_index.py — run this once
import chromadb
from sentence_transformers import SentenceTransformer
import os

model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection("regulations")

def chunk_text(text, size=300, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), size - overlap):
        chunk = ' '.join(words[i:i+size])
        if len(chunk) > 80:
            chunks.append(chunk)
    return chunks

for fname in os.listdir("reg_docs"):
    fpath = f"reg_docs/{fname}"
    with open(fpath, 'r') as f:
        text = f.read()
    
    chunks = chunk_text(text)
    embeddings = model.encode(chunks).tolist()
    source_name = fname.replace('.txt','').replace('.pdf','')
    
    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[f"{source_name}_{i}" for i in range(len(chunks))],
        metadatas=[{"source": source_name} for _ in chunks]
    )
    print(f"Indexed {len(chunks)} chunks from {fname}")

print("RAG index built!")
```

```bash
python3 build_rag_index.py
```

---

## STEP 11 — Verify Everything Works

```bash
# Terminal 1: Start Redis (if not running as service)
redis-server

# Terminal 2: Start Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Check it works:
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Terminal 3: Start Frontend
cd frontend
npm run dev

# Open: http://localhost:3000
```

---

## QUICK INSTALL VERIFICATION CHECKLIST

```bash
# Run this to check all key packages installed correctly
python3 - << 'EOF'
packages = [
    ("fastapi", "fastapi"),
    ("pandas", "pandas"),
    ("fairlearn", "fairlearn"),
    ("aif360", "aif360"),
    ("shap", "shap"),
    ("anthropic", "anthropic"),
    ("chromadb", "chromadb"),
    ("sentence_transformers", "sentence_transformers"),
    ("weasyprint", "weasyprint"),
    ("redis", "redis"),
    ("sklearn", "scikit-learn"),
    ("imblearn", "imbalanced-learn"),
]

print("Checking installations...\n")
all_good = True
for import_name, pip_name in packages:
    try:
        __import__(import_name)
        print(f"  OK  {pip_name}")
    except ImportError:
        print(f"  MISSING  {pip_name}  →  pip install {pip_name}")
        all_good = False

print("\nAll good!" if all_good else "\nFix missing packages above, then re-run.")
EOF
```

---

## COMMON ERRORS + FIXES

| Error | Fix |
|---|---|
| `WeasyPrint` fails on Linux | `sudo apt install libcairo2 libpango-1.0-0 libpangocairo-1.0-0` |
| `psycopg2` build fails | Use `psycopg2-binary` instead |
| `aif360` install slow | Normal — it pulls large datasets, wait 3–5 min |
| `sentence-transformers` first run slow | Downloads model (~90MB) on first use, cached after |
| `chromadb` sqlite error on Linux | `pip install pysqlite3-binary` |
| CORS error in browser | Check `allow_origins=["*"]` in FastAPI CORS middleware |
| Redis connection refused | Run `redis-server` or `sudo systemctl start redis` |
| Port 8000 in use | `uvicorn main:app --port 8001` and update `.env.local` |

---

## TOTAL INSTALL TIME ESTIMATE

| Step | Time |
|---|---|
| System deps | 5 min |
| Python packages | 8–12 min (aif360 is slow) |
| Node packages | 2 min |
| Demo datasets download | 1 min |
| RAG index build | 2 min |
| **Total** | **~20 min** |

---

*After all steps pass — go straight to STEPS.md and start building.*