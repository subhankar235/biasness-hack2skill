#  schma file--

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


# ── Helpers ──────────────────────────────────────────────────────────────────

def now_utc():
    return datetime.utcnow()

def new_uuid():
    return str(uuid.uuid4())


# ── Org / Auth ────────────────────────────────────────────────────────────────

class Org(Base):
    __tablename__ = "orgs"

    id         = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    name       = Column(String(255), nullable=False)
    slug       = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=now_utc)

    users    = relationship("User", back_populates="org")
    datasets = relationship("Dataset", back_populates="org")
    models   = relationship("MLModel", back_populates="org")


class User(Base):
    __tablename__ = "users"

    id             = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id         = Column(UUID(as_uuid=False), ForeignKey("orgs.id"), nullable=False)
    email          = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active      = Column(Boolean, default=True)
    is_superuser   = Column(Boolean, default=False)
    created_at     = Column(DateTime, default=now_utc)

    org = relationship("Org", back_populates="users")


# ── Datasets ──────────────────────────────────────────────────────────────────

class Dataset(Base):
    __tablename__ = "datasets"

    id         = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id     = Column(UUID(as_uuid=False), ForeignKey("orgs.id"), nullable=False)
    name       = Column(String(255), nullable=False)
    s3_key     = Column(String(512), nullable=False)        # path in S3/MinIO
    row_count  = Column(Integer)
    col_count  = Column(Integer)
    profile    = Column(JSONB)                              # ydata-profiling output
    created_at = Column(DateTime, default=now_utc)

    org         = relationship("Org", back_populates="datasets")
    bias_runs   = relationship("BiasRun", back_populates="dataset")
    counterfactual_results = relationship("CounterfactualResult", back_populates="dataset", lazy="selectin")


# ── ML Models ─────────────────────────────────────────────────────────────────

class MLModel(Base):
    __tablename__ = "ml_models"

    id           = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id       = Column(UUID(as_uuid=False), ForeignKey("orgs.id"), nullable=False)
    name         = Column(String(255), nullable=False)
    version      = Column(String(50))
    framework    = Column(String(50))                       # sklearn, onnx, xgboost …
    s3_key       = Column(String(512), nullable=False)
    input_schema = Column(JSONB)                            # feature names + dtypes
    created_at   = Column(DateTime, default=now_utc)

    org       = relationship("Org", back_populates="models")
    bias_runs = relationship("BiasRun", back_populates="model")
    shap_runs = relationship("ShapRun", back_populates="model")
    counterfactual_results = relationship("CounterfactualResult", back_populates="model", lazy="selectin")


# ── Bias / Fairness ───────────────────────────────────────────────────────────

class BiasRun(Base):
    __tablename__ = "bias_runs"

    id                = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    dataset_id        = Column(UUID(as_uuid=False), ForeignKey("datasets.id"), nullable=False)
    model_id          = Column(UUID(as_uuid=False), ForeignKey("ml_models.id"), nullable=True)
    sensitive_attrs   = Column(JSONB)                       # ["gender","race"]
    scorecard         = Column(JSONB)                       # aif360 + fairlearn metrics
    heatmap           = Column(JSONB)                       # contingency table per group
    intersectional    = Column(JSONB)                       # combo metrics
    status            = Column(String(20), default="pending")  # pending/running/done/error
    created_at        = Column(DateTime, default=now_utc)
    completed_at      = Column(DateTime, nullable=True)

    dataset      = relationship("Dataset", back_populates="bias_runs")
    model        = relationship("MLModel", back_populates="bias_runs")
    narratives   = relationship("Narrative", back_populates="bias_run")
    remediations = relationship("Remediation", back_populates="bias_run")
    reports      = relationship("Report", back_populates="bias_run")


class ShapRun(Base):
    __tablename__ = "shap_runs"

    id         = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    model_id   = Column(UUID(as_uuid=False), ForeignKey("ml_models.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=False), ForeignKey("datasets.id"), nullable=False)
    shap_values = Column(JSONB)                             # per-group SHAP
    status     = Column(String(20), default="pending")
    created_at = Column(DateTime, default=now_utc)

    model = relationship("MLModel", back_populates="shap_runs")


# ── Remediation ───────────────────────────────────────────────────────────────

class Remediation(Base):
    __tablename__ = "remediations"

    id           = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    bias_run_id  = Column(UUID(as_uuid=False), ForeignKey("bias_runs.id"), nullable=False)
    strategy     = Column(String(50))                       # reweigh / threshold / smote
    params       = Column(JSONB)
    before_metrics = Column(JSONB)
    after_metrics  = Column(JSONB)
    created_at   = Column(DateTime, default=now_utc)

    bias_run = relationship("BiasRun", back_populates="remediations")


# ── Narratives ────────────────────────────────────────────────────────────────

class Narrative(Base):
    __tablename__ = "narratives"

    id          = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    bias_run_id = Column(UUID(as_uuid=False), ForeignKey("bias_runs.id"), nullable=False)
    prompt_key  = Column(String(100))                       # which j2 template was used
    content     = Column(Text)
    model_used  = Column(String(100))
    created_at  = Column(DateTime, default=now_utc)

    bias_run = relationship("BiasRun", back_populates="narratives")


# ── Monitoring ────────────────────────────────────────────────────────────────

class MonitoringEvent(Base):
    __tablename__ = "monitoring_events"

    id         = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id     = Column(UUID(as_uuid=False), ForeignKey("orgs.id"), nullable=False)
    model_id   = Column(UUID(as_uuid=False), ForeignKey("ml_models.id"), nullable=True)
    payload    = Column(JSONB)
    metric_snapshot = Column(JSONB)
    received_at = Column(DateTime, default=now_utc)


# ── Reports ───────────────────────────────────────────────────────────────────

class Report(Base):
    __tablename__ = "reports"

    id          = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    bias_run_id = Column(UUID(as_uuid=False), ForeignKey("bias_runs.id"), nullable=False)
    s3_key      = Column(String(512))
    sha256      = Column(String(64))
    created_at  = Column(DateTime, default=now_utc)

    bias_run = relationship("BiasRun", back_populates="reports")


# ── Benchmark ─────────────────────────────────────────────────────────────────

class BenchmarkEntry(Base):
    __tablename__ = "benchmark_entries"
    __table_args__ = (UniqueConstraint("org_id", "metric_key", name="uq_org_metric"),)

    id         = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id     = Column(UUID(as_uuid=False), ForeignKey("orgs.id"), nullable=False)
    metric_key = Column(String(100))                        # e.g. "demographic_parity"
    value      = Column(Float)
    percentile = Column(Float)
    updated_at = Column(DateTime, default=now_utc)


# ── Counterfactual ────────────────────────────────────────────────────────────

class CounterfactualResult(Base):
    __tablename__ = "counterfactual_results"
    __table_args__ = (
        UniqueConstraint("model_id", "dataset_id", "row_index", "desired_outcome",
                         name="uq_cf_model_dataset_row_outcome"),
    )

    id = Column(UUID(as_uuid=False), primary_key=True, default=new_uuid)
    org_id = Column(UUID(as_uuid=False), ForeignKey("orgs.id"), nullable=False)
    model_id = Column(UUID(as_uuid=False), ForeignKey("ml_models.id"), nullable=False)
    dataset_id = Column(UUID(as_uuid=False), ForeignKey("datasets.id"), nullable=False)

    row_index = Column(Integer, nullable=False)
    desired_outcome = Column(Integer, nullable=False)
    method = Column(String(32), nullable=False, default="greedy")

    num_candidates = Column(Integer, nullable=False, default=0)
    best_composite_score = Column(Float, nullable=True)
    elapsed_seconds = Column(Float, nullable=True)

    s3_result_key = Column(Text, nullable=True)

    created_at = Column(DateTime, default=now_utc)
    updated_at = Column(DateTime, default=now_utc)

    is_stale = Column(Boolean, default=False, nullable=False)

    model = relationship("MLModel", back_populates="counterfactual_results", lazy="selectin")
    dataset = relationship("Dataset", back_populates="counterfactual_results", lazy="selectin")