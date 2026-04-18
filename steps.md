# FairLens — AI Bias Detection: Complete Build Guide

> **Stack at a glance:** Python 3.11 · FastAPI · Next.js 14 · Tailwind CSS · PostgreSQL · Redis · ChromaDB · Claude API (Anthropic)

---

## PROJECT STRUCTURE

```
fairlens/
├── backend/
│   ├── main.py                  # FastAPI app entry
│   ├── routers/
│   │   ├── upload.py            # Dataset upload + profiling
│   │   ├── analyze.py           # Bias metrics
│   │   ├── narrative.py         # Claude LLM pipeline
│   │   ├── intersectional.py    # Intersectional analysis
│   │   ├── counterfactual.py    # Counterfactual testing
│   │   ├── remediation.py       # Bias remediation wizard
│   │   ├── rag.py               # Regulation Q&A
│   │   └── export.py            # PDF export
│   ├── services/
│   │   ├── profiler.py
│   │   ├── fairness.py
│   │   ├── explainer.py
│   │   └── llm.py
│   ├── templates/
│   │   └── audit_report.html    # Jinja2 PDF template
│   ├── reg_docs/                # EEOC, GDPR, EU AI Act PDFs
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── app/
│   │   ├── page.tsx             # Upload page
│   │   ├── report/[id]/page.tsx # Report page
│   │   └── layout.tsx
│   ├── components/
│   │   ├── Dropzone.tsx
│   │   ├── ProfileCard.tsx
│   │   ├── ScorecardGrid.tsx
│   │   ├── BiasHeatmap.tsx
│   │   ├── FindingsList.tsx
│   │   ├── RemediationWizard.tsx
│   │   └── RagChat.tsx
│   ├── package.json
│   └── .env.local
└── docker-compose.yml
```

---

## PHASE 1 — HOURS 0–6: FOUNDATION

### STEP 1 — Project Scaffold

**Tools:** Python 3.11, pip, Node.js 18+, PostgreSQL, Redis

```bash
# Backend
mkdir fairlens && cd fairlens
python -m venv venv && source venv/bin/activate
mkdir backend && cd backend
pip install fastapi uvicorn[standard] python-multipart python-dotenv \
            psycopg2-binary sqlalchemy redis

# Start FastAPI skeleton
# backend/main.py:
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FairLens API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health(): return {"status": "ok"}

# Run:
uvicorn main:app --reload --port 8000
```

```bash
# Frontend
cd ../
npx create-next-app@latest frontend --typescript --tailwind --app --no-git
cd frontend
npm install axios react-dropzone recharts @radix-ui/react-tabs lucide-react
npm run dev  # runs on http://localhost:3000
```

---

### STEP 2 — CSV Upload Endpoint

**Tools:** `fastapi`, `pandas`, `python-multipart`
**Why:** Foundation of everything. All other features depend on a dataset being loaded.

```bash
pip install pandas ydata-profiling sentence-transformers
```

```python
# backend/routers/upload.py
import pandas as pd
import io, uuid, json
from fastapi import APIRouter, UploadFile, File
from ydata_profiling import ProfileReport
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

router = APIRouter()
model = SentenceTransformer('all-MiniLM-L6-v2')

SENSITIVE_KEYWORDS = ['gender','sex','race','ethnicity','age','postcode',
                      'zip','nationality','religion','disability','marital']

SENSITIVE_EMBEDDINGS = model.encode(SENSITIVE_KEYWORDS)

def detect_sensitive(col_name: str) -> tuple[bool, float]:
    """Returns (is_sensitive, confidence_score)"""
    col_lower = col_name.lower().replace('_',' ')
    # Exact match
    if any(k in col_lower for k in SENSITIVE_KEYWORDS):
        return True, 1.0
    # Embedding similarity
    col_emb = model.encode([col_lower])
    sims = cosine_similarity(col_emb, SENSITIVE_EMBEDDINGS)[0]
    max_sim = float(np.max(sims))
    return (max_sim > 0.60), round(max_sim, 3)

@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    
    # YData profiling (minimal=True is fast — ~3 seconds)
    profile = ProfileReport(df, minimal=True, progress_bar=False)
    profile_json = json.loads(profile.to_json())
    
    # Sensitive attribute detection
    sensitive_cols = []
    for col in df.columns:
        is_sensitive, confidence = detect_sensitive(col)
        if is_sensitive:
            sensitive_cols.append({
                "column": col,
                "confidence": confidence,
                "dtype": str(df[col].dtype),
                "unique_values": df[col].nunique()
            })
    
    dataset_id = str(uuid.uuid4())[:8]
    # Store df to temp (use Redis or disk)
    df.to_parquet(f"/tmp/{dataset_id}.parquet")
    
    return {
        "dataset_id": dataset_id,
        "rows": len(df),
        "columns": list(df.columns),
        "sensitive_columns": sensitive_cols,
        "profile": {
            col: {
                "missing_pct": round(profile_json["variables"][col].get("p_missing", 0)*100, 1),
                "type": profile_json["variables"][col].get("type"),
                "distinct": profile_json["variables"][col].get("n_distinct")
            }
            for col in df.columns if col in profile_json.get("variables", {})
        }
    }
```

```python
# backend/main.py — register router
from routers.upload import router as upload_router
app.include_router(upload_router, prefix="/api")
```

**Frontend — Dropzone component:**

```tsx
// frontend/components/Dropzone.tsx
'use client'
import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'

export default function Dropzone({ onResult }: { onResult: (data: any) => void }) {
  const [loading, setLoading] = useState(false)

  const onDrop = useCallback(async (files: File[]) => {
    setLoading(true)
    const formData = new FormData()
    formData.append('file', files[0])
    const { data } = await axios.post('http://localhost:8000/api/upload', formData)
    onResult(data)
    setLoading(false)
  }, [onResult])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept: { 'text/csv': ['.csv'] } })

  return (
    <div {...getRootProps()} className={`border-2 border-dashed rounded-xl p-16 text-center cursor-pointer transition-colors
      ${isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'}`}>
      <input {...getInputProps()} />
      {loading ? <p className="text-gray-500">Analyzing dataset...</p>
               : <p className="text-gray-500">Drop a CSV file here, or click to browse</p>}
    </div>
  )
}
```

**Milestone check:** Upload `german_credit.csv` → JSON response shows `age`, `sex` flagged as sensitive. ✓

---

## PHASE 2 — HOURS 6–24: CORE FEATURES

### STEP 3 — Multi-Metric Bias Scorecard

**Tools:** `fairlearn`, `scipy`, `numpy`, `aif360`
**Tech:** FastAPI endpoint + React card grid + Recharts for CI visualization

```bash
pip install fairlearn aif360 scikit-learn scipy
```

```python
# backend/routers/analyze.py
import pandas as pd
import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel
from fairlearn.metrics import (
    demographic_parity_difference,
    equalized_odds_difference,
    MetricFrame
)
from sklearn.metrics import confusion_matrix
from scipy.stats import bootstrap

router = APIRouter()

class AnalyzeRequest(BaseModel):
    dataset_id: str
    sensitive_col: str
    target_col: str
    prediction_col: str = None   # optional — if model preds already in CSV

def bootstrap_ci(func, data_tuple, n_resamples=500):
    """Returns (point_estimate, ci_low, ci_high)"""
    result = bootstrap(data_tuple, func, n_resamples=n_resamples,
                       confidence_level=0.95, random_state=42)
    point = func(*data_tuple)
    return float(point), float(result.confidence_interval.low), float(result.confidence_interval.high)

@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    df = pd.read_parquet(f"/tmp/{req.dataset_id}.parquet")
    
    y_true = df[req.target_col]
    sensitive = df[req.sensitive_col]
    
    # If no prediction col, use target as proxy (demo mode)
    y_pred = df[req.prediction_col] if req.prediction_col else y_true
    
    results = []
    
    # 1. Demographic Parity Difference
    def dp_func(y_true, y_pred, sensitive):
        return demographic_parity_difference(y_true, y_pred, sensitive_features=sensitive)
    
    point, ci_low, ci_high = bootstrap_ci(
        lambda a, b, c: demographic_parity_difference(a, b, sensitive_features=c),
        (y_true.values, y_pred.values, sensitive.values)
    )
    results.append({
        "metric": "Demographic Parity Difference",
        "value": round(point, 4),
        "ci_low": round(ci_low, 4),
        "ci_high": round(ci_high, 4),
        "threshold": 0.1,
        "status": "fail" if abs(point) > 0.2 else "warn" if abs(point) > 0.1 else "pass",
        "description": "Difference in selection rates between groups. Ideal = 0."
    })
    
    # 2. Equalized Odds Difference
    point, ci_low, ci_high = bootstrap_ci(
        lambda a, b, c: equalized_odds_difference(a, b, sensitive_features=c),
        (y_true.values, y_pred.values, sensitive.values)
    )
    results.append({
        "metric": "Equalized Odds Difference",
        "value": round(point, 4),
        "ci_low": round(ci_low, 4),
        "ci_high": round(ci_high, 4),
        "threshold": 0.1,
        "status": "fail" if abs(point) > 0.2 else "warn" if abs(point) > 0.1 else "pass",
        "description": "Max difference in TPR and FPR between groups. Ideal = 0."
    })
    
    # 3. Disparate Impact Ratio (4/5ths rule)
    groups = sensitive.unique()
    rates = {g: float((y_pred[sensitive == g] == 1).mean()) for g in groups}
    max_rate = max(rates.values())
    min_rate = min(rates.values())
    di_ratio = min_rate / max_rate if max_rate > 0 else 1.0
    results.append({
        "metric": "Disparate Impact Ratio",
        "value": round(di_ratio, 4),
        "ci_low": None,
        "ci_high": None,
        "threshold": 0.8,
        "status": "fail" if di_ratio < 0.8 else "warn" if di_ratio < 0.9 else "pass",
        "description": "Ratio of favorable outcome rates. EEOC 4/5ths rule requires > 0.8.",
        "group_rates": {str(k): round(v, 4) for k, v in rates.items()}
    })
    
    return {"dataset_id": req.dataset_id, "metrics": results}
```

**Frontend — ScorecardGrid:**

```tsx
// frontend/components/ScorecardGrid.tsx
const STATUS_COLORS = {
  pass: 'bg-green-50 border-green-200 text-green-800',
  warn: 'bg-amber-50 border-amber-200 text-amber-800',
  fail: 'bg-red-50 border-red-200 text-red-800'
}

export default function ScorecardGrid({ metrics }: { metrics: any[] }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {metrics.map(m => (
        <div key={m.metric} className={`rounded-xl border p-4 ${STATUS_COLORS[m.status]}`}>
          <p className="text-xs font-medium uppercase tracking-wide opacity-70">{m.metric}</p>
          <p className="text-3xl font-semibold mt-1">{m.value}</p>
          {m.ci_low && (
            <p className="text-xs mt-1 opacity-60">95% CI: [{m.ci_low}, {m.ci_high}]</p>
          )}
          <p className="text-xs mt-2 opacity-80">{m.description}</p>
          <span className={`inline-block mt-2 text-xs font-bold uppercase px-2 py-0.5 rounded
            ${m.status === 'pass' ? 'bg-green-200' : m.status === 'warn' ? 'bg-amber-200' : 'bg-red-200'}`}>
            {m.status}
          </span>
        </div>
      ))}
    </div>
  )
}
```

---

### STEP 4 — Group Disparity Heatmap

**Tools:** `pandas` (groupby + pivot), `Recharts` (frontend heatmap)
**Tech:** FastAPI `/heatmap` endpoint → React component with click drill-down

```python
# backend/routers/analyze.py — add to existing router

@router.post("/heatmap")
def heatmap(dataset_id: str, col_x: str, col_y: str, target_col: str):
    df = pd.read_parquet(f"/tmp/{dataset_id}.parquet")
    
    pivot = df.groupby([col_x, col_y])[target_col].agg(['mean','count']).reset_index()
    pivot.columns = [col_x, col_y, 'rate', 'count']
    
    # Convert to heatmap-friendly format
    matrix = []
    for _, row in pivot.iterrows():
        matrix.append({
            "x": str(row[col_x]),
            "y": str(row[col_y]),
            "rate": round(float(row['rate']), 4),
            "count": int(row['count'])
        })
    
    overall_rate = float(df[target_col].mean())
    return {"matrix": matrix, "overall_rate": overall_rate}
```

```tsx
// frontend/components/BiasHeatmap.tsx
// Use Recharts ScatterChart or a simple CSS grid heatmap
// Color scale: white (low rate) → red (high rate, high disparity)
// Each cell shows rate + click → opens drill-down modal with subset stats
```

---

### STEP 5 — LLM Bias Narrative Engine (MOST IMPORTANT)

**Tools:** `anthropic` Python SDK, `redis` (caching), structured JSON output
**Tech:** FastAPI `/narrative` endpoint → Claude API → parsed findings array → React FindingsList

```bash
pip install anthropic redis
```

```python
# backend/routers/narrative.py
import json, hashlib, os
from fastapi import APIRouter
from pydantic import BaseModel
import anthropic
import redis as redis_lib

router = APIRouter()
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
cache = redis_lib.Redis(host='localhost', port=6379, db=0)

class NarrativeRequest(BaseModel):
    dataset_id: str
    metrics: list
    sensitive_col: str
    dataset_name: str = "uploaded dataset"

SYSTEM_PROMPT = """You are a senior AI fairness auditor with expertise in anti-discrimination law.
You receive bias metric results and produce structured audit findings.
Return ONLY a valid JSON array. No preamble, no markdown, no explanation outside the JSON.

Each finding object must have exactly these fields:
- finding_id: string (F001, F002, etc.)
- severity: string (critical | high | medium | low)
- title: string (one sentence, specific, no jargon)
- description: string (2-3 sentences with specific numbers from the metrics)
- feature_driver: string (which column is driving this bias)
- legal_risk: string (which regulation this may violate, one sentence)
- recommendation: string (one concrete, actionable fix)"""

@router.post("/narrative")
def generate_narrative(req: NarrativeRequest):
    # Cache key from metrics content
    cache_key = f"narrative:{hashlib.md5(json.dumps(req.metrics, sort_keys=True).encode()).hexdigest()}"
    cached = cache.get(cache_key)
    if cached:
        return {"findings": json.loads(cached), "cached": True}
    
    user_content = f"""
Dataset: {req.dataset_name}
Sensitive attribute analyzed: {req.sensitive_col}

BIAS METRICS:
{json.dumps(req.metrics, indent=2)}

Generate audit findings for all metrics with status 'warn' or 'fail'.
Include at least one finding per failing metric.
Be specific with numbers. Reference {req.sensitive_col} by name.
"""
    
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}]
    )
    
    text = response.content[0].text.strip()
    # Strip markdown code fences if present
    text = text.replace("```json","").replace("```","").strip()
    findings = json.loads(text)
    
    # Cache for 24 hours
    cache.setex(cache_key, 86400, json.dumps(findings))
    return {"findings": findings, "cached": False}
```

```tsx
// frontend/components/FindingsList.tsx
const SEVERITY_STYLES = {
  critical: 'border-l-4 border-red-500 bg-red-50',
  high:     'border-l-4 border-orange-500 bg-orange-50',
  medium:   'border-l-4 border-amber-500 bg-amber-50',
  low:      'border-l-4 border-blue-500 bg-blue-50',
}

export default function FindingsList({ findings }) {
  return (
    <div className="space-y-4">
      {findings.map(f => (
        <div key={f.finding_id} className={`rounded-r-xl p-4 ${SEVERITY_STYLES[f.severity]}`}>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono text-gray-400">{f.finding_id}</span>
            <span className="text-xs font-bold uppercase">{f.severity}</span>
          </div>
          <h3 className="font-medium text-gray-900">{f.title}</h3>
          <p className="text-sm text-gray-700 mt-1">{f.description}</p>
          <p className="text-xs text-gray-500 mt-2">⚖ {f.legal_risk}</p>
          <p className="text-sm font-medium text-gray-800 mt-2">→ {f.recommendation}</p>
        </div>
      ))}
    </div>
  )
}
```

---

### STEP 6 — Intersectional Bias Analysis

**Tools:** `pandas`, `itertools`, `scipy.stats`, `fairlearn`
**Tech:** FastAPI `/intersectional` endpoint → React ranked findings table

```python
# backend/routers/intersectional.py
import pandas as pd
import numpy as np
import itertools
from fastapi import APIRouter
from pydantic import BaseModel
from scipy.stats import chi2_contingency

router = APIRouter()

class IntersectionalRequest(BaseModel):
    dataset_id: str
    sensitive_cols: list[str]    # e.g. ["sex", "age_bucket", "race"]
    target_col: str
    min_group_size: int = 30

@router.post("/intersectional")
def intersectional_analysis(req: IntersectionalRequest):
    df = pd.read_parquet(f"/tmp/{req.dataset_id}.parquet")
    overall_rate = float(df[req.target_col].mean())
    results = []
    
    # 2-way and 3-way combinations
    for r in range(2, min(4, len(req.sensitive_cols) + 1)):
        for combo in itertools.combinations(req.sensitive_cols, r):
            combo = list(combo)
            df['_group_key'] = df[combo].astype(str).agg(' × '.join, axis=1)
            
            for group_val, subset in df.groupby('_group_key'):
                n = len(subset)
                if n < req.min_group_size:
                    continue
                
                group_rate = float(subset[req.target_col].mean())
                disparity_ratio = group_rate / overall_rate if overall_rate > 0 else 1.0
                
                # Statistical significance (chi2 test)
                contingency = pd.crosstab(
                    df['_group_key'] == group_val,
                    df[req.target_col]
                )
                if contingency.shape == (2, 2):
                    _, p_value, _, _ = chi2_contingency(contingency)
                else:
                    p_value = 1.0
                
                if p_value < 0.05:  # only statistically significant findings
                    results.append({
                        "group_label": group_val,
                        "dimensions": combo,
                        "n": n,
                        "decision_rate": round(group_rate, 4),
                        "overall_rate": round(overall_rate, 4),
                        "disparity_ratio": round(disparity_ratio, 3),
                        "p_value": round(p_value, 4),
                        "severity": (
                            "critical" if disparity_ratio > 2.5 or disparity_ratio < 0.4 else
                            "high"     if disparity_ratio > 2.0 or disparity_ratio < 0.5 else
                            "medium"   if disparity_ratio > 1.5 or disparity_ratio < 0.67 else
                            "low"
                        )
                    })
    
    del df['_group_key']
    
    # Sort by absolute disparity
    results.sort(key=lambda x: abs(x['disparity_ratio'] - 1), reverse=True)
    
    return {
        "overall_rate": round(overall_rate, 4),
        "total_groups_tested": len(results),
        "significant_disparities": [r for r in results if r['severity'] in ['critical','high']],
        "all_results": results[:50]  # cap at 50 for UI performance
    }
```

---

### STEP 7 — Audit PDF Export

**Tools:** `WeasyPrint`, `jinja2`, `hashlib`, `datetime`
**Tech:** FastAPI `/export` endpoint → browser download

```bash
pip install weasyprint jinja2
```

```python
# backend/routers/export.py
import hashlib
from datetime import datetime, timezone
from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

router = APIRouter()
jinja_env = Environment(loader=FileSystemLoader("templates"))

class ExportRequest(BaseModel):
    dataset_name: str
    analyst_name: str
    org_name: str
    metrics: list
    findings: list
    intersectional: list = []

@router.post("/export")
def export_pdf(req: ExportRequest):
    template = jinja_env.get_template("audit_report.html")
    
    html_content = template.render(
        dataset_name=req.dataset_name,
        analyst_name=req.analyst_name,
        org_name=req.org_name,
        analysis_date=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        metrics=req.metrics,
        findings=req.findings,
        intersectional=req.intersectional,
        methodology="Fairlearn 0.10 · Bootstrap CI n=500 · Claude claude-opus-4-5 · FairLens v1.0"
    )
    
    pdf_bytes = HTML(string=html_content).write_pdf()
    doc_hash = hashlib.sha256(pdf_bytes).hexdigest()[:16].upper()
    
    filename = f"FairLens_Audit_{req.dataset_name}_{datetime.now().strftime('%Y%m%d')}_{doc_hash}.pdf"
    
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}",
                 "X-Document-Hash": doc_hash}
    )
```

```html
<!-- backend/templates/audit_report.html -->
<!DOCTYPE html>
<html>
<head>
<style>
  body { font-family: Arial, sans-serif; font-size: 12px; color: #1a1a1a; margin: 40px; }
  h1 { font-size: 22px; font-weight: bold; border-bottom: 2px solid #1a1a1a; padding-bottom: 8px; }
  h2 { font-size: 16px; margin-top: 28px; color: #333; }
  .meta { color: #666; font-size: 11px; }
  .metric-pass { background: #f0fdf4; border-left: 4px solid #16a34a; padding: 8px 12px; margin: 6px 0; }
  .metric-warn { background: #fffbeb; border-left: 4px solid #d97706; padding: 8px 12px; margin: 6px 0; }
  .metric-fail { background: #fef2f2; border-left: 4px solid #dc2626; padding: 8px 12px; margin: 6px 0; }
  .finding { border: 1px solid #e5e7eb; border-radius: 6px; padding: 12px; margin: 10px 0; }
  .finding-critical { border-left: 5px solid #dc2626; }
  .finding-high { border-left: 5px solid #ea580c; }
  .finding-medium { border-left: 5px solid #d97706; }
  .footer { margin-top: 40px; font-size: 10px; color: #999; border-top: 1px solid #e5e7eb; padding-top: 12px; }
  .sign-off { margin-top: 40px; display: flex; gap: 60px; }
  .sign-off-box { border-bottom: 1px solid #333; width: 200px; height: 40px; }
</style>
</head>
<body>
<h1>AI Bias Audit Report — FairLens</h1>
<p class="meta">
  Organization: <strong>{{ org_name }}</strong> &nbsp;|&nbsp;
  Dataset: <strong>{{ dataset_name }}</strong> &nbsp;|&nbsp;
  Date: {{ analysis_date }} &nbsp;|&nbsp;
  Analyst: {{ analyst_name }}
</p>

<h2>Bias Metrics Summary</h2>
{% for m in metrics %}
<div class="metric-{{ m.status }}">
  <strong>{{ m.metric }}:</strong> {{ m.value }}
  {% if m.ci_low %} (95% CI: [{{ m.ci_low }}, {{ m.ci_high }}]){% endif %}
  — <em>{{ m.status | upper }}</em> (threshold: {{ m.threshold }})
</div>
{% endfor %}

<h2>Audit Findings</h2>
{% for f in findings %}
<div class="finding finding-{{ f.severity }}">
  <p><strong>{{ f.finding_id }} [{{ f.severity | upper }}]</strong> — {{ f.title }}</p>
  <p>{{ f.description }}</p>
  <p><em>Legal risk:</em> {{ f.legal_risk }}</p>
  <p><strong>Recommendation:</strong> {{ f.recommendation }}</p>
</div>
{% endfor %}

{% if intersectional %}
<h2>Intersectional Findings</h2>
{% for r in intersectional[:10] %}
<div class="finding finding-{{ r.severity }}">
  <strong>{{ r.group_label }}</strong> (n={{ r.n }}):
  Decision rate {{ r.decision_rate }} vs overall {{ r.overall_rate }}
  — Disparity ratio {{ r.disparity_ratio }}× [{{ r.severity | upper }}]
</div>
{% endfor %}
{% endif %}

<h2>Methodology</h2>
<p>{{ methodology }}</p>
<p>This report was generated automatically by FairLens. Results should be reviewed by a qualified fairness expert before legal use.</p>

<div class="sign-off">
  <div><p>Analyst sign-off</p><div class="sign-off-box"></div><p>{{ analyst_name }}</p></div>
  <div><p>Approver sign-off</p><div class="sign-off-box"></div><p>_________________</p></div>
</div>

<div class="footer">
  Generated by FairLens v1.0 · {{ analysis_date }} · Methodology: {{ methodology }}
  <!-- Hash appended to filename, not footer, for tamper evidence -->
</div>
</body>
</html>
```

---

## PHASE 3 — HOURS 24–36: DIFFERENTIATORS

### STEP 8 — Counterfactual Fairness Testing

**Tools:** `pandas`, `numpy`, `joblib`/`onnxruntime`, `shap`
**Tech:** FastAPI `/counterfactual` endpoint → React result card

```bash
pip install shap onnxruntime joblib
```

```python
# backend/routers/counterfactual.py
import pandas as pd
import numpy as np
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
import joblib, io

router = APIRouter()

class CounterfactualRequest(BaseModel):
    dataset_id: str
    sensitive_col: str
    prediction_col: str   # model predictions already in CSV
    n_samples: int = 500

@router.post("/counterfactual")
def counterfactual_test(req: CounterfactualRequest):
    df = pd.read_parquet(f"/tmp/{req.dataset_id}.parquet")
    sample = df.sample(n=min(req.n_samples, len(df)), random_state=42)
    
    unique_vals = df[req.sensitive_col].unique()
    
    changed = []
    unchanged = []
    
    for idx, row in sample.iterrows():
        original_pred = row[req.prediction_col]
        original_group = row[req.sensitive_col]
        
        # Test flipping to each other group value
        for alt_val in unique_vals:
            if alt_val == original_group:
                continue
            # We only have predictions in CSV, so we measure:
            # what % of people in alt_group with similar features get different outcomes
            # Proxy: compare original_pred to median prediction of alt_group
            alt_group_pred = df[df[req.sensitive_col] == alt_val][req.prediction_col].median()
            original_pred_val = float(original_pred)
            
            # For binary predictions
            if abs(original_pred_val - float(alt_group_pred)) > 0.5:
                changed.append({
                    "original_group": str(original_group),
                    "counterfactual_group": str(alt_val),
                    "original_pred": original_pred_val,
                    "alt_pred": float(alt_group_pred)
                })
            else:
                unchanged.append(idx)
    
    unfairness_score = len(changed) / (len(changed) + len(unchanged)) if (changed or unchanged) else 0
    
    # Group rates for comparison
    group_rates = {}
    for val in unique_vals:
        mask = df[req.sensitive_col] == val
        group_rates[str(val)] = round(float(df.loc[mask, req.prediction_col].mean()), 4)
    
    return {
        "counterfactual_unfairness_score": round(unfairness_score, 4),
        "n_tested": len(sample),
        "n_would_change": len(changed),
        "verdict": "fail" if unfairness_score > 0.15 else "warn" if unfairness_score > 0.05 else "pass",
        "group_rates": group_rates,
        "interpretation": f"{round(unfairness_score*100, 1)}% of predictions would likely change if the '{req.sensitive_col}' attribute were different."
    }
```

---

### STEP 9 — Regulation Q&A (RAG)

**Tools:** `chromadb`, `sentence-transformers`, `pypdf2`, `anthropic`
**Tech:** FastAPI `/rag` endpoint → React chat-style Q&A component

```bash
pip install chromadb sentence-transformers pypdf2
```

```python
# backend/services/rag_index.py — run once to build index
import chromadb
from sentence_transformers import SentenceTransformer
import PyPDF2, os, json

model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")

REG_DOCS = {
    "eeoc": "reg_docs/eeoc_uniform_guidelines.pdf",
    "gdpr_22": "reg_docs/gdpr_article22.pdf",
    "eu_ai_act": "reg_docs/eu_ai_act_title3.pdf",
    "uk_equality": "reg_docs/uk_equality_act.pdf"
}

def chunk_text(text: str, chunk_size=400, overlap=50) -> list[str]:
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i+chunk_size])
        if len(chunk) > 100:
            chunks.append(chunk)
    return chunks

def build_index():
    collection = chroma_client.get_or_create_collection("regulations")
    
    for reg_name, pdf_path in REG_DOCS.items():
        if not os.path.exists(pdf_path):
            print(f"Missing: {pdf_path} — skipping")
            continue
        
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ' '.join(page.extract_text() or '' for page in reader.pages)
        
        chunks = chunk_text(text)
        embeddings = model.encode(chunks).tolist()
        
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=[f"{reg_name}_{i}" for i in range(len(chunks))],
            metadatas=[{"source": reg_name, "chunk_idx": i} for i in range(len(chunks))]
        )
        print(f"Indexed {len(chunks)} chunks from {reg_name}")

if __name__ == "__main__":
    build_index()
```

```python
# backend/routers/rag.py
import os
import chromadb
from sentence_transformers import SentenceTransformer
from fastapi import APIRouter
from pydantic import BaseModel
import anthropic

router = APIRouter()
model = SentenceTransformer('all-MiniLM-L6-v2')
chroma_client = chromadb.PersistentClient(path="./chroma_db")
claude = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

class RagRequest(BaseModel):
    question: str
    scorecard: list = []    # current model's metrics (for context)

@router.post("/rag")
def rag_query(req: RagRequest):
    collection = chroma_client.get_collection("regulations")
    
    q_embedding = model.encode([req.question]).tolist()
    results = collection.query(query_embeddings=q_embedding, n_results=5)
    
    context_chunks = results['documents'][0]
    sources = [m['source'] for m in results['metadatas'][0]]
    context = "\n\n---\n\n".join(context_chunks)
    
    prompt = f"""You are a legal expert in AI fairness regulations.

REGULATION CONTEXT:
{context}

CURRENT MODEL BIAS SCORECARD:
{req.scorecard if req.scorecard else "Not provided"}

QUESTION: {req.question}

Answer the question using ONLY the regulation context above.
Be specific. Cite regulation names and sections in [brackets].
If the current scorecard shows a violation, say so explicitly.
Keep response under 200 words."""

    response = claude.messages.create(
        model="claude-opus-4-5",
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}]
    )
    
    return {
        "answer": response.content[0].text,
        "sources": list(set(sources)),
        "question": req.question
    }
```

```tsx
// frontend/components/RagChat.tsx
// Simple: text input → POST /api/rag → display answer with sources
// Style as a chat bubble. Sources shown as small chips below answer.
```

---

### STEP 10 — Remediation Wizard

**Tools:** `fairlearn` (ExponentiatedGradient), `imbalanced-learn` (SMOTENC), `sklearn`
**Tech:** FastAPI `/remediate` endpoint → React before/after split view

```bash
pip install imbalanced-learn
```

```python
# backend/routers/remediation.py
import pandas as pd
import numpy as np
from fastapi import APIRouter
from pydantic import BaseModel
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_curve
from fairlearn.reductions import ExponentiatedGradient, DemographicParity
from fairlearn.metrics import demographic_parity_difference
from imblearn.over_sampling import SMOTENC

router = APIRouter()

class RemediationRequest(BaseModel):
    dataset_id: str
    sensitive_col: str
    target_col: str
    strategy: str   # "reweight" | "resample" | "threshold"

@router.post("/remediate")
def remediate(req: RemediationRequest):
    df = pd.read_parquet(f"/tmp/{req.dataset_id}.parquet")
    
    # Encode categoricals for ML
    df_enc = pd.get_dummies(df.drop(columns=[req.target_col, req.sensitive_col]))
    X = df_enc
    y = df[req.target_col]
    sensitive = df[req.sensitive_col]
    
    # Before metrics
    baseline_model = LogisticRegression(max_iter=500).fit(X, y)
    y_pred_before = baseline_model.predict(X)
    before_dp = float(demographic_parity_difference(y, y_pred_before, sensitive_features=sensitive))
    before_rate = {str(g): round(float((y_pred_before[sensitive == g]).mean()), 4)
                   for g in sensitive.unique()}
    
    if req.strategy == "reweight":
        mitigator = ExponentiatedGradient(
            LogisticRegression(max_iter=500),
            DemographicParity()
        )
        mitigator.fit(X, y, sensitive_features=sensitive)
        y_pred_after = mitigator.predict(X)
        method_description = "Exponentiated Gradient with Demographic Parity constraint (Fairlearn)"
        
    elif req.strategy == "resample":
        cat_indices = [i for i, c in enumerate(X.columns) if X[c].dtype == 'uint8']
        sm = SMOTENC(categorical_features=cat_indices, random_state=42)
        X_res, y_res = sm.fit_resample(X, y)
        new_model = LogisticRegression(max_iter=500).fit(X_res, y_res)
        y_pred_after = new_model.predict(X)
        method_description = "SMOTENC oversampling to balance group representation"
        
    elif req.strategy == "threshold":
        y_proba = baseline_model.predict_proba(X)[:, 1]
        thresholds = {}
        for group in sensitive.unique():
            mask = sensitive == group
            fpr, tpr, thresh = roc_curve(y[mask], y_proba[mask])
            # Youden's J: maximize TPR - FPR
            best_idx = np.argmax(tpr - fpr)
            thresholds[str(group)] = round(float(thresh[best_idx]), 4)
        
        y_pred_after = np.array([
            1 if y_proba[i] >= thresholds[str(sensitive.iloc[i])] else 0
            for i in range(len(y))
        ])
        method_description = f"Per-group optimal thresholds: {thresholds}"
    
    after_dp = float(demographic_parity_difference(y, y_pred_after, sensitive_features=sensitive))
    after_rate = {str(g): round(float((y_pred_after[sensitive == g]).mean()), 4)
                  for g in sensitive.unique()}
    
    improvement_pct = round(abs(before_dp - after_dp) / abs(before_dp) * 100, 1) if before_dp != 0 else 0
    
    return {
        "strategy": req.strategy,
        "method_description": method_description,
        "before": {"demographic_parity_difference": round(before_dp, 4), "group_rates": before_rate},
        "after":  {"demographic_parity_difference": round(after_dp, 4), "group_rates": after_rate},
        "improvement_pct": improvement_pct,
        "verdict": "improved" if abs(after_dp) < abs(before_dp) else "no_improvement"
    }
```

```tsx
// frontend/components/RemediationWizard.tsx
// Three buttons: "Reweight" | "Resample" | "Threshold"
// On select → POST /api/remediate → show before/after card side by side
// Before card (red/amber) → After card (green)
// Show improvement_pct as a big number: "42% reduction in disparity"
```

---

## ENVIRONMENT SETUP

```bash
# backend/.env
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://user:pass@localhost:5432/fairlens
REDIS_URL=redis://localhost:6379
STORAGE_PATH=/tmp/fairlens_datasets
```

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

```bash
# requirements.txt
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-multipart==0.0.9
pandas==2.2.2
ydata-profiling==4.8.3
sentence-transformers==2.7.0
scikit-learn==1.4.2
fairlearn==0.10.0
aif360==0.6.1
scipy==1.13.0
numpy==1.26.4
shap==0.45.0
onnxruntime==1.18.0
imbalanced-learn==0.12.2
anthropic==0.25.0
redis==5.0.4
chromadb==0.5.0
PyPDF2==3.0.1
jinja2==3.1.4
weasyprint==62.3
sqlalchemy==2.0.30
psycopg2-binary==2.9.9
python-dotenv==1.0.1
```

---

## DEMO DATASET SETUP

Download these free datasets to demo instantly (no need to wait for user upload):

```python
# backend/demo_data.py — pre-load COMPAS and German Credit for instant demo
import pandas as pd

# German Credit (1000 rows, sex + age sensitive attributes, credit risk target)
# Download: https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data
# COMPAS Recidivism (7000 rows, race sensitive, two_year_recid target)
# Download: https://github.com/propublica/compas-analysis/raw/master/compas-scores-two-years.csv

def load_compas():
    url = "https://raw.githubusercontent.com/propublica/compas-analysis/master/compas-scores-two-years.csv"
    df = pd.read_csv(url)
    df = df[['age','sex','race','priors_count','decile_score','two_year_recid']].dropna()
    df['prediction'] = (df['decile_score'] >= 5).astype(int)
    df.to_parquet("/tmp/demo_compas.parquet")
    return "demo_compas"

def load_german_credit():
    # Use AIF360 built-in
    from aif360.datasets import GermanDataset
    gd = GermanDataset()
    df = gd.convert_to_dataframe()[0]
    df.to_parquet("/tmp/demo_german.parquet")
    return "demo_german"
```

---

## DEPLOYMENT (30 MINUTES)

```bash
# Frontend → Vercel
cd frontend
npx vercel --prod
# Set env var NEXT_PUBLIC_API_URL to your Railway backend URL

# Backend → Railway
# 1. Push to GitHub
# 2. New Railway project → Deploy from GitHub → select backend folder
# 3. Add env vars: ANTHROPIC_API_KEY, DATABASE_URL (Railway PostgreSQL), REDIS_URL (Railway Redis)
# 4. Add Procfile: web: uvicorn main:app --host 0.0.0.0 --port $PORT

# Procfile
echo "web: uvicorn main:app --host 0.0.0.0 --port \$PORT" > Procfile
```

---

## TECH STACK QUICK REFERENCE

| Feature | Backend | ML/AI Libraries | Frontend | Storage |
|---|---|---|---|---|
| Dataset Upload | FastAPI + python-multipart | pandas, ydata-profiling, sentence-transformers | react-dropzone | Parquet on disk |
| Bias Scorecard | FastAPI | fairlearn, aif360, scipy, numpy | Recharts, Tailwind | Redis (cache) |
| Heatmap | FastAPI | pandas groupby | Recharts ScatterChart | — |
| LLM Narrative | FastAPI | anthropic SDK | React components | Redis (24h cache) |
| Intersectional | FastAPI | pandas, itertools, scipy.stats | React table | — |
| Counterfactual | FastAPI | pandas, numpy, sklearn | React card | — |
| Reg Q&A (RAG) | FastAPI | chromadb, sentence-transformers, anthropic | Chat-style UI | ChromaDB (disk) |
| Remediation | FastAPI | fairlearn, imbalanced-learn, sklearn | Before/after split | — |
| PDF Export | FastAPI | WeasyPrint, jinja2, hashlib | Download button | — |
| Demo Data | FastAPI | aif360, pandas | Pre-loaded selector | Parquet on disk |

---

*FairLens — Built in 36 hours. Detects what others miss.*