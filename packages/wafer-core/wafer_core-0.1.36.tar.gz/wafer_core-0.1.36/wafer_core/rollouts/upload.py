"""Upload evaluation results to Supabase Storage."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

SUPABASE_URL = "https://hvlpthcnxlywlquiciqe.supabase.co"
BUCKET_NAME = "traces"
API_BASE = os.environ.get("WAFER_API_URL", "https://api.wafer.ai")


def upload_results_to_supabase(output_dir: Path, log: logging.Logger | None = None) -> bool:
    """Upload results to Supabase Storage.

    Requires SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY env var.

    Args:
        output_dir: Path to results directory (must contain report.json)
        log: Optional logger

    Returns:
        True if upload succeeded, False otherwise
    """
    if log is None:
        log = logger

    # Check for report.json
    if not (output_dir / "report.json").exists():
        log.warning(f"No report.json in {output_dir}, skipping upload")
        return False

    # Check for Supabase key
    supabase_key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_ANON_KEY")
    if not supabase_key:
        log.warning("SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY not set, skipping upload")
        return False

    try:
        from supabase import create_client

        client = create_client(SUPABASE_URL, supabase_key)
        run_name = output_dir.name
        uploaded = []

        # Upload report.json
        report_path = output_dir / "report.json"
        storage_path = f"{run_name}/report.json"
        with open(report_path, "rb") as f:
            client.storage.from_(BUCKET_NAME).upload(
                storage_path,
                f.read(),
                {"content-type": "application/json", "upsert": "true"},
            )
        uploaded.append("report.json")

        # Upload samples/*.json
        samples_dir = output_dir / "samples"
        if samples_dir.exists():
            for sample_file in samples_dir.glob("*.json"):
                storage_path = f"{run_name}/samples/{sample_file.name}"
                with open(sample_file, "rb") as f:
                    client.storage.from_(BUCKET_NAME).upload(
                        storage_path,
                        f.read(),
                        {"content-type": "application/json", "upsert": "true"},
                    )
                uploaded.append(sample_file.name)

        # Update manifest
        manifest_path = "_manifest.json"
        try:
            data = client.storage.from_(BUCKET_NAME).download(manifest_path)
            manifest = json.loads(data)
        except Exception:
            manifest = {"runs": []}

        if run_name not in manifest["runs"]:
            manifest["runs"].append(run_name)
            manifest["runs"].sort(reverse=True)

            # Remove old manifest first (upsert doesn't always work)
            try:
                client.storage.from_(BUCKET_NAME).remove([manifest_path])
            except Exception:
                pass

            client.storage.from_(BUCKET_NAME).upload(
                manifest_path,
                json.dumps(manifest, indent=2).encode(),
                {"content-type": "application/json"},
            )

        log.info(f"Uploaded {len(uploaded)} files to Supabase: {run_name}")

        # Auto-index in database for trace viewer
        # Fail if indexing fails - user can re-run (everything is idempotent)
        if not _index_run_in_database(run_name, report_path, log):
            return False

        return True

    except ImportError:
        log.warning("supabase package not installed, skipping upload")
        return False
    except Exception as e:
        log.error(f"Failed to upload to Supabase: {e}")
        return False


def _index_run_in_database(run_name: str, report_path: Path, log: logging.Logger) -> bool:
    """Index a run in the trace_runs database table for fast querying.

    Calls POST /v1/eval-traces/runs to upsert the run metadata.
    This enables the trace viewer to show the run immediately without manual sync.

    Args:
        run_name: Name of the run (folder name)
        report_path: Path to the report.json file
        log: Logger instance

    Returns:
        True if indexing succeeded, False otherwise
    """
    try:
        with open(report_path) as f:
            report = json.load(f)

        response = httpx.post(
            f"{API_BASE}/v1/eval-traces/runs",
            json={"name": run_name, "report": report},
            timeout=30.0,
        )

        if response.status_code == 200:
            log.info(f"Indexed run in database: {run_name}")
            return True
        else:
            log.error(f"Failed to index run {run_name}: {response.status_code} {response.text}")
            return False

    except Exception as e:
        log.error(f"Failed to index run {run_name} in database: {e}")
        return False
