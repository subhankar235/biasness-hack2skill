# FairLens - Detect Hidden Bias Before It Hurts Real People

## Overview
FairLens helps organizations detect and reduce hidden bias in machine learning models before deployment. It combines fairness metrics, explainability tools, and actionable remediation insights through an intuitive dashboard built for real-world impact.

### *Detect bias. Enforce fairness. Build trust.*

Most tools only tell you a model is biased.

**FairLens shows who is harmed, why it happens, and how to fix it.**

> **FairLens** is an end-to-end bias detection and mitigation platform for high-stakes ML systems — purpose-built for hiring, lending, and healthcare decisions where a flawed model doesn't just fail metrics, it fails people.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com/)

---

## Built MVP Features

- CSV / Dataset Upload
- Fairness Metrics Dashboard
- SHAP Explainability Insights
- Bias Mitigation Recommendations
- Exportable Audit Reports

---

## 🧠 Problem Statement

Every day, ML models make decisions that shape lives:
- A resume screener **rejects a qualified candidate** because the model learned gender proxies from historical hiring data.
- A credit scoring model **denies a loan** to a minority applicant with the same risk profile as an approved white applicant.
- A clinical triage model **under-prioritizes patients** from underserved communities due to biased training labels.

These aren't edge cases — they're systematic failures baked into production systems. The real danger? **Most teams don't know their model is biased until it makes headlines.**

Current tools are either:
- Too academic (IBM AIF360, Fairlearn) — hard to integrate, no UX
- Too shallow (just demographic parity checks) — miss intersectional and proxy bias
- Too passive — detect but never fix

**FairLens closes the gap: from raw dataset to actionable debiasing recommendations, in one unified platform.**

---

## 💡 Solution Overview

FairLens is a **full-stack fairness auditing system** that plugs into your existing ML pipeline and outputs:

- **Quantified bias scores** across 6 fairness metrics
- **Root cause attribution** (which features/slices drive bias)
- **Counterfactual simulations** (what would change the model's decision?)
- **Automated fix recommendations** (reweighting, resampling, threshold calibration)
- **Audit-ready PDF reports** for compliance and stakeholder review

### Key Capabilities

- 🔍 **Detects 5 types of bias**: dataset, model, proxy, intersectional, label bias
- 📐 **Evaluates 6 fairness metrics**: Demographic Parity, Equalized Odds, Calibration, Individual Fairness, Counterfactual Fairness, Predictive Parity
- 🧬 **Explains decisions** using SHAP values + LLM-generated plain-language summaries
- 🔧 **Recommends mitigations** ranked by impact-vs-effort score
- 📊 **Monitors drift** — catches bias that emerges post-deployment

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          FairLens AI Pipeline                           │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐     ┌──────────────────┐     ┌────────────────────┐
  │  DATA LAYER  │────▶│  BIAS DETECTION  │────▶│ FAIRNESS METRICS   │
  │              │     │                  │     │                    │
  │ CSV / DB /   │     │ • Stat. Parity   │     │ • Dem. Parity Gap  │
  │ API / Model  │     │ • Proxy Detector │     │ • Eq. Odds Delta   │
  │ Predictions  │     │ • Label Audit    │     │ • Calibration Err  │
  │              │     │ • Slice Analysis │     │ • Indiv. Fairness  │
  └──────────────┘     └──────────────────┘     └────────────────────┘
                                                          │
  ┌──────────────┐     ┌──────────────────┐     ┌────────▼───────────┐
  │   FRONTEND   │◀────│  RECOMMENDATION  │◀────│  EXPLAINABILITY    │
  │  DASHBOARD   │     │     ENGINE       │     │                    │
  │              │     │                  │     │ • SHAP Attribution │
  │ • Bias Map   │     │ • Reweighting    │     │ • LLM Narration    │
  │ • Risk Score │     │ • Resampling     │     │ • Feature Impact   │
  │ • Fix Panel  │     │ • Threshold Adj  │     │ • Counterfactuals  │
  │ • PDF Report │     │ • Ranked by ROI  │     │ • Slice Heatmaps   │
  └──────────────┘     └──────────────────┘     └────────────────────┘
                                   │
                          ┌────────▼────────┐
                          │   LLM LAYER     │
                          │  Claude Sonnet  │
                          │  (Narration +   │
                          │   Fix Drafting) │
                          └─────────────────┘
```

### Pipeline Stages

1. **Data Ingestion** — Upload CSV datasets or connect live model endpoints via REST. Auto-detects schema, sensitive attributes (race, gender, age), and target variables.

2. **Bias Detection** — Runs statistical disparity tests (χ², KS-test, Wasserstein distance) across protected groups. Flags proxy features (e.g., zip code as a racial proxy) using mutual information scoring.

3. **Fairness Evaluation** — Computes 6 industry-standard fairness metrics. Generates a composite **FairLens Score (0–100)** with per-metric breakdowns and threshold alerts.

4. **Explainability** — Uses SHAP to attribute model decisions per demographic slice. Claude Sonnet translates SHAP outputs into plain English risk summaries for non-technical stakeholders.

5. **Recommendation Engine** — Ranks mitigation strategies by `impact_score / implementation_cost`. Outputs ranked, actionable fixes with code snippets.

---

## ⚙️ Tech Stack

### 🔧 Backend
| Tool | Why |
|------|-----|
| **FastAPI** | High-performance async REST API; auto-generates OpenAPI docs |
| **Celery + Redis** | Offloads long-running bias scans to background task queue |
| **Pandas / NumPy** | Core data wrangling and statistical computation |
| **Scikit-learn** | Model evaluation, preprocessing, and baseline classifiers |

### 🎨 Frontend
| Tool | Why |
|------|-----|
| **React 18** | Component-based UI with concurrent rendering for real-time updates |
| **Recharts** | Declarative chart library — renders bias heatmaps and fairness radar |
| **TailwindCSS** | Rapid utility-first styling without design debt |
| **Framer Motion** | Smooth transitions for score reveal and report animations |

### 🤖 ML / Fairness
| Tool | Why |
|------|-----|
| **IBM AIF360** | Battle-tested fairness metrics and reweighing algorithms |
| **Fairlearn** | Grid search mitigation and equalized odds post-processing |
| **SHAP** | Model-agnostic feature attribution for explainability layer |
| **SciPy** | Statistical hypothesis testing (χ², KS, ANOVA) |

### 🗄️ Database
| Tool | Why |
|------|-----|
| **PostgreSQL** | Stores audit logs, scan results, and historical fairness drift |
| **SQLAlchemy** | ORM with async support for non-blocking DB operations |

### 🧠 AI (LLM)
| Tool | Why |
|------|-----|
| **Claude Sonnet (Anthropic)** | Converts raw SHAP/metric outputs into human-readable risk summaries and mitigation narratives. Also generates structured compliance reports via prompt-chaining. |

### 🚀 DevOps
| Tool | Why |
|------|-----|
| **Docker + Compose** | Reproducible local dev and deployment; isolates ML deps |
| **GitHub Actions** | CI pipeline: linting, unit tests, fairness regression tests on PRs |

---

## 🚀 Features

### 🟢 Core Features (MVP)

**📂 Dataset Bias Scanner**
Ingests tabular datasets and runs automated demographic disparity analysis. Computes group-level distributions, label imbalance ratios, and flags features with high mutual information to protected attributes (proxy bias detection).

**📐 Fairness Score Engine**
Evaluates 6 fairness metrics in parallel and synthesizes a single **FairLens Score**. Each metric is weighted by domain context (e.g., equalized odds weighted higher in healthcare than lending).

**🔬 Model Bias Checker**
Accepts model predictions (CSV or live endpoint) and evaluates post-hoc fairness across demographic slices. Works with **any model** — XGBoost, neural nets, proprietary APIs — no retraining needed.

**💬 Risk Explanation Engine**
SHAP values are computed per protected group and fed to Claude Sonnet, which generates a 3-sentence natural language summary: *what the bias is, why it exists, and who it harms*. Output is calibrated for both technical and executive audiences.

**📊 Fairness Dashboard**
Interactive React dashboard with: radar chart (fairness metrics), demographic parity bar chart, SHAP waterfall plots, and a top-3 recommended fixes panel. Exportable to PDF in one click.

---

### 🟡 Advanced Features

**🔄 Counterfactual Simulation**
"What would change this prediction?" — Users input a flagged individual's features and the system computes the **minimum feature change** needed to flip the model's output. Exposes discriminatory decision boundaries.

**🔍 Root Cause Analyzer**
Traces bias back to its origin: dataset collection, labeling process, feature engineering, or model architecture. Uses causal graph analysis (DoWhy) to distinguish *proxy bias* from *direct discrimination*.

**🔧 Fix Recommendation Engine**
Generates ranked mitigation strategies with estimated fairness gain and implementation cost. Provides ready-to-run Python code snippets for: reweighing, adversarial debiasing, threshold optimization, and calibrated equalization.

**📄 Report Generator**
One-click PDF audit report: executive summary, full metric breakdown, SHAP explanations, identified risk groups, and recommended remediations. Formatted for regulatory compliance (EEOC, ECOA, EU AI Act).

---

### 🔴 Future / WOW Features

**🤖 AI Fairness Agent**
An autonomous Claude-powered agent that: monitors your model endpoint, detects bias drift in real time, drafts a mitigation PR, and pings your Slack channel — all without human intervention.

**📈 Bias Drift Monitoring**
Tracks fairness metrics over time as production data evolves. Fires alerts when scores degrade beyond configurable thresholds. Built for MLOps integration (MLflow, Weights & Biases).

**🌐 Federated Audit Mode**
Audit models without ever accessing raw data — FairLens computes fairness metrics locally on the data owner's infrastructure and returns only aggregated statistics.

---

## ⚡ How It Works

```
User uploads dataset/model
         │
         ▼
FastAPI receives file → validates schema → detects sensitive columns
         │
         ▼
Celery worker triggers bias scan pipeline (async)
         │
    ┌────┴────────────────────────────┐
    │                                 │
    ▼                                 ▼
Dataset Audit                  Model Prediction Audit
(AIF360 + SciPy)               (SHAP + Fairlearn)
    │                                 │
    └────────────┬────────────────────┘
                 │
                 ▼
        Fairness Metrics Engine
        (6 metrics → FairLens Score)
                 │
                 ▼
        SHAP Attribution per Group
                 │
                 ▼
        Claude Sonnet API call
        (structured prompt → plain-English risk narrative)
                 │
                 ▼
        Recommendation Engine
        (ranked fixes with code snippets)
                 │
                 ▼
        Results stored in PostgreSQL
                 │
                 ▼
        React Dashboard renders live
        (WebSocket push on scan completion)
                 │
                 ▼
        User exports PDF audit report
```

---

## 🧪 Demo

**Dataset Used:** COMPAS Recidivism Dataset (ProPublica, n=7,214)
> A real-world criminal justice dataset used to predict recidivism risk — one of the most studied cases of algorithmic bias in public policy.

**Bias Detected:**
- Black defendants were **1.97× more likely** to be falsely flagged as high-risk than white defendants
- Demographic Parity Gap: **0.34** (industry threshold: < 0.10)
- Equalized Odds Delta: **0.28** (false positive rate disparity)

**What the User Sees:**
1. FairLens Score: **32 / 100** 🔴 (Critical Risk)
2. Risk narrative from Claude: *"The model exhibits significant racial disparity in false positive rates. Black defendants face nearly double the likelihood of incorrect high-risk classification compared to white defendants with identical criminal history profiles. This likely traces to biased historical labeling in the training data."*
3. Top fix: Reweighing preprocessing (estimated score improvement: +28 points)

---

## 📊 Example Output

```json
{
  "fairlens_score": 32,
  "risk_level": "CRITICAL",
  "metrics": {
    "demographic_parity_gap": 0.34,
    "equalized_odds_delta": 0.28,
    "calibration_error": 0.11,
    "individual_fairness_score": 0.61,
    "counterfactual_fairness": 0.54,
    "predictive_parity_gap": 0.19
  },
  "highest_risk_group": "Black defendants (false positive rate: 44.8%)",
  "proxy_features_detected": ["zip_code", "prior_arrests_juvenile"],
  "explanation": "The model exhibits significant racial disparity in false positive rates...",
  "recommendations": [
    {
      "strategy": "Reweighing (Pre-processing)",
      "expected_score_gain": 28,
      "implementation_effort": "LOW",
      "code_snippet": "rw = Reweighing(unprivileged_groups, privileged_groups)\nrw.fit(dataset_orig_train)\ndataset_transf = rw.transform(dataset_orig_train)"
    },
    {
      "strategy": "Equalized Odds Post-processing",
      "expected_score_gain": 22,
      "implementation_effort": "MEDIUM",
      "code_snippet": "..."
    }
  ]
}
```

---

## 🏆 Why This Stands Out

- **Full pipeline, not a library** — FairLens isn't a Python package you import. It's a deployable product with UI, API, database, and LLM layer working together. No other hackathon project does this end-to-end.

- **LLM-augmented explainability** — We don't just report numbers. Claude Sonnet turns cryptic fairness metrics into narratives that a hiring manager, loan officer, or hospital administrator can act on.

- **Model-agnostic by design** — Works with any model via prediction CSVs or API endpoints. No access to model internals required. Audits proprietary black-box systems.

- **Compliance-aware output** — Reports are structured around EEOC, ECOA, and EU AI Act requirements. This isn't just a research tool — it's an enterprise compliance instrument.

- **Counterfactual + root cause in one** — Most tools tell you *that* a model is biased. FairLens tells you *why*, *where it came from*, and *how to fix it* — with ranked, code-ready recommendations.

---

## ⚠️ Challenges & Solutions

| Challenge | Solution |
|-----------|----------|
| SHAP computation is slow on large datasets | Implemented background Celery tasks + TreeExplainer (100× faster than KernelExplainer) |
| LLM outputs inconsistent explanation formats | Used structured JSON prompting with Claude + Pydantic validation layer |
| Fairness metrics conflict with each other (impossibility theorem) | Added metric priority configuration per domain (hiring vs. lending vs. healthcare) |
| Proxy bias is hard to detect automatically | Mutual information scoring between all features and protected attributes, threshold-configurable |
| Users don't know which mitigation to choose | Built impact/effort scoring matrix; surfaces top pick with estimated FairLens Score improvement |

---

## 🔮 Future Scope

- **Regulatory Compliance Packs** — Pre-built profiles for GDPR Article 22, EU AI Act Annex III, EEOC Uniform Guidelines
- **MLflow / W&B Integration** — Native plugin for fairness tracking alongside existing ML experiment logs
- **Multi-model Comparison** — Audit 2–5 candidate models simultaneously and surface the fairest one
- **Real-time Streaming Audit** — Kafka-based pipeline for monitoring live prediction streams at scale

---

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/subhankar235/biasness-hack2skill.git
cd biasness-hack2skill

# 2. Set environment variables
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# 3. Start all services with Docker
docker-compose up --build

# --- OR run manually ---

# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Celery worker (separate terminal)
celery -A app.worker worker --loglevel=info

# Frontend
cd frontend
npm install
npm run dev
```

### Access
| Service | URL |
|---------|-----|
| Frontend Dashboard | http://localhost:3000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| Celery Monitor | http://localhost:5555 |

### Run Your First Audit

```bash
curl -X POST http://localhost:8000/api/v1/scan \
  -F "file=@your_dataset.csv" \
  -F "target_column=loan_approved" \
  -F "sensitive_columns=race,gender" \
  -F "domain=lending"
```

---



---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">

**FairLens** — Because the cost of biased AI isn't a metric. It's a person.

*Built at Hack2Skill 2026*

</div>
