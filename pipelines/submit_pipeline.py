import os
from google.cloud import aiplatform

# Constants - ensure these match or are loaded dynamically
PROJECT_ID = "helpful-girder-421422"
REGION = "us-central1"
PIPELINE_ROOT = "gs://trade-mlops-bucket/pipeline_root"
PIPELINE_JSON = "trading_pipeline.json"

# Service Account
SERVICE_ACCOUNT = "akamlops@helpful-girder-421422.iam.gserviceaccount.com"

# Credential Setup
CREDENTIALS_DIR = r"D:\work\GOOGLE_APPLICATION_CREDENTIALS"
CREDENTIALS_FILE = "helpful-girder-421422-ee6bb27e5b9a.json"
CREDENTIALS_PATH = os.path.join(CREDENTIALS_DIR, CREDENTIALS_FILE)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

if not os.path.exists(CREDENTIALS_PATH):
    print(f"[ERROR] Credential file not found at: {CREDENTIALS_PATH}")
    print("Please ensure the file exists and is a valid JSON key file.")

def submit_pipeline_job():
    aiplatform.init(project=PROJECT_ID, location=REGION)

    job = aiplatform.PipelineJob(
        display_name="trading-pipeline-job",
        template_path=PIPELINE_JSON,
        pipeline_root=PIPELINE_ROOT,
        enable_caching=True,
    )

    print("Submitting pipeline job...")
    job.submit(service_account=SERVICE_ACCOUNT)
    # SDK already prints the dashboard URI
    print("Job submitted successfully.")

if __name__ == "__main__":
    submit_pipeline_job()
