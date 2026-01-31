from datetime import datetime
from urllib.parse import quote

from werkzeug.exceptions import BadRequest

from cidc_api.models import IngestionJobs
from . import gcloud_client
from ..shared.auth import get_current_user

JOB_TYPE_ASSAY = "assay"
JOB_TYPE_CLINICAL = "clinical"
ALLOWED_JOB_TYPES = {JOB_TYPE_CLINICAL, JOB_TYPE_ASSAY}


def resolve_job_type_and_assay_fields(data: dict) -> tuple[str, str | None, str | None]:
    """Decide job_type and gather assay_type/batch_id from request JSON."""
    assay_type = data.get("assay_type")
    # If job_type is assay or assay_type is present, treat this as an assay job.
    job_type = data.get("job_type") or (JOB_TYPE_ASSAY if assay_type else JOB_TYPE_CLINICAL)

    if job_type not in ALLOWED_JOB_TYPES:
        raise BadRequest("Invalid job_type. Allowed values are 'clinical' or 'assay'.")

    if job_type == JOB_TYPE_ASSAY and (not assay_type or not isinstance(assay_type, str)):
        raise BadRequest("assay_type must be provided for job_type='assay'.")

    assay_type = assay_type.strip() if assay_type else None
    batch_id = data.get("batch_id").strip() if isinstance(data.get("batch_id"), str) else None

    return job_type, assay_type, batch_id


def prepare_assay_job(trial_id: str, assay_type: str, batch_id: str) -> tuple[str, str, str, datetime, int, str]:
    """
    Validate assay job uniqueness and generate submission_id, start_date, version, and the trial’s GCS intake path.
    """
    if not assay_type:
        raise BadRequest("assay_type must be provided for job_type='assay'.")

    # Enforce uniqueness of (trial_id, assay_type, batch_id) when batch_id is present.
    if batch_id:
        existing_job = IngestionJobs.get_unique_assay_job(trial_id, assay_type, batch_id)
        if existing_job:
            raise BadRequest(
                f"Assay job {existing_job.id} already exists for this exact trial_id/assay_type/batch_id combination."
            )

    submission_id = IngestionJobs.next_assay_submission_id(trial_id, assay_type)
    job_status = "INITIAL SUBMISSION"
    error_status = "Upload Incomplete"  # job starts with 'Incomplete' notifier
    start_date = datetime.now()
    version = 1

    # Create or retrieve intake bucket corresponding to the trial
    intake_bucket = gcloud_client.create_intake_bucket(get_current_user().email, trial_id=trial_id)
    gcs_path = f"{intake_bucket.name}/{assay_type}/{submission_id}"

    return submission_id, job_status, error_status, start_date, version, gcs_path


def get_google_links(intake_path: str) -> tuple[str, str]:
    """Build the GCS URI and GCS Console URL corresponding to the intake path."""
    gcs_uri = f"gs://{intake_path}"
    # Encode path to ensure link opens correctly
    encoded_path = quote(intake_path)
    console_url = f"https://console.cloud.google.com/storage/browser/{encoded_path}"

    return gcs_uri, console_url
