import re


class CustomAttributeError(Exception):
    """Custom error for setting read-only properties."""

    pass


def extract_error_message(error_text):
    """
    Extract the core error message between 'Bad Request - error creating job:'
    and 'the request is not valid'
    """
    pattern = r"Bad Request - error creating job:?\s*(.*?)(?:the request is not valid|$)"
    match = re.search(pattern, error_text, re.DOTALL | re.IGNORECASE)

    if match:
        return match.group(1).strip()[:-1]
    else:
        return error_text


def wrap_user(payload: dict) -> dict:
    """Wraps a dictionary payload in a user / reference structure."""
    return {"user": payload, "system": {"references": []}}


def extract_all_table_paths(dataset_dict: dict) -> list[str]:
    """Extract all table source paths from tables and task sources."""
    # Extract table sources
    table_paths = [table["source"] for table in dataset_dict.get("tables", []) if "source" in table]

    # Extract and filter task sources (remove None values)
    task_sources = dataset_dict.get("task", {}).get("source", {})
    task_paths = [path for path in task_sources.values() if path is not None]

    return table_paths + task_paths


def build_view_name(table_path: str, job_id: str, app_name: str) -> str:
    """Convert table path to corresponding view name by inserting job_id."""
    _, _, table = table_path.split(".")
    job_suffix = job_id.replace("-", "_")
    return f"{app_name}.RESULTS.job_{job_suffix}_{table}"


def get_results_views(job_status: dict, app_name: str) -> dict:
    """Extract view names for predictions and embeddings from completed job."""
    if job_status["status"] != "COMPLETED":
        return None

    job_id = job_status["job_id"]
    export_paths = job_status["export_paths"]

    results_views = {}

    if "predictions" in export_paths:
        results_views["predictions"] = {build_view_name(export_paths["predictions"], job_id, app_name)}

    if "embeddings" in export_paths:
        results_views["embeddings"] = {
            node_id: build_view_name(path, job_id, app_name) for node_id, path in export_paths["embeddings"].items()
        }

    return results_views
