# app/tasks/remediation_tasks.py
import asyncio
import logging

from app.tasks.celery_app import celery_app
from app.core.remediation import run_remediation
from app.storage.s3 import download_parquet

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _save_result(remediation_id: str, result: dict) -> None:
    """
    Synchronous DB write — Celery workers run in sync context.
    Uses a fresh SQLAlchemy sync engine (not the async one used by FastAPI).
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.config import settings
    from app.db.models import Remediation

    # Swap asyncpg → psycopg2 for sync Celery context
    sync_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg", "postgresql+psycopg2"
    ).split("?")[0]   # strip SSL params — psycopg2 handles SSL differently

    engine = create_engine(sync_url, connect_args={"sslmode": "require"})

    with Session(engine) as session:
        record = session.get(Remediation, remediation_id)
        if not record:
            logger.error("Remediation record %s not found", remediation_id)
            return

        record.before_metrics = result.get("before")
        record.after_metrics = {
            "method_description": result.get("method_description"),
            "demographic_parity_difference": result.get("after", {}).get("demographic_parity_difference"),
            "equalized_odds_difference": result.get("after", {}).get("equalized_odds_difference"),
            "group_rates": result.get("after", {}).get("group_rates"),
            "improvement_pct": result.get("improvement_pct"),
            "verdict": result.get("verdict"),
            "group_thresholds": result.get("group_thresholds"),  # threshold strategy only
        }
        session.commit()

    engine.dispose()


def _download_sync(s3_key: str):
    """Run the async S3 download in a sync context for Celery."""
    return asyncio.get_event_loop().run_until_complete(download_parquet(s3_key))


# ─────────────────────────────────────────────
# Celery Task
# ─────────────────────────────────────────────

@celery_app.task(
    bind=True,
    name="app.tasks.remediation_tasks.run_reweigh_task",
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def run_reweigh_task(
    self,
    remediation_id: str,
    s3_key: str,
    sensitive_col: str,
    target_col: str,
) -> dict:
    return run_remediation_task(remediation_id, s3_key, sensitive_col, target_col, "reweight").result()


@celery_app.task(
    bind=True,
    name="app.tasks.remediation_tasks.run_threshold_task",
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def run_threshold_task(
    self,
    remediation_id: str,
    s3_key: str,
    sensitive_col: str,
    target_col: str,
) -> dict:
    return run_remediation_task(remediation_id, s3_key, sensitive_col, target_col, "threshold").result()


@celery_app.task(
    bind=True,
    name="app.tasks.remediation_tasks.run_smote_task",
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def run_smote_task(
    self,
    remediation_id: str,
    s3_key: str,
    sensitive_col: str,
    target_col: str,
) -> dict:
    return run_remediation_task(remediation_id, s3_key, sensitive_col, target_col, "smote").result()


@celery_app.task(
    bind=True,
    name="app.tasks.remediation_tasks.run_remediation_task",
    max_retries=2,
    default_retry_delay=10,
    acks_late=True,
)
def run_remediation_task(
    self,
    remediation_id: str,
    s3_key: str,
    sensitive_col: str,
    target_col: str,
    strategy: str,
) -> dict:
    """
    Celery task: download dataset → run remediation → persist result.

    Args:
        remediation_id: UUID of the Remediation DB record
        s3_key:         S3/MinIO path to the parquet dataset
        sensitive_col:  protected attribute column name
        target_col:     ground truth / label column name
        strategy:       one of reweight | resample | threshold

    Returns:
        result dict (also written to DB)
    """
    logger.info(
        "[remediation:%s] Starting strategy=%s dataset=%s",
        remediation_id, strategy, s3_key,
    )

    try:
        # 1. Load dataset
        df = _download_sync(s3_key)
        logger.info("[remediation:%s] Loaded %d rows", remediation_id, len(df))

        # Validate columns exist
        missing = [c for c in [sensitive_col, target_col] if c not in df.columns]
        if missing:
            raise ValueError(f"Columns not found in dataset: {missing}")

        # 2. Run remediation logic
        result = run_remediation(
            df=df,
            sensitive_col=sensitive_col,
            target_col=target_col,
            strategy=strategy,
        )

        logger.info(
            "[remediation:%s] Done. improvement_pct=%.1f verdict=%s",
            remediation_id,
            result.get("improvement_pct", 0),
            result.get("verdict"),
        )

        # 3. Persist to DB
        _save_result(remediation_id, result)

        return result

    except Exception as exc:
        logger.exception("[remediation:%s] Failed: %s", remediation_id, exc)
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            # Write error state to DB so the polling endpoint doesn't hang
            _save_result(remediation_id, {
                "before": None,
                "after": {"error": str(exc)},
                "method_description": f"FAILED: {exc}",
                "improvement_pct": None,
                "verdict": "error",
            })
            raise