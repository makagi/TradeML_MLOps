from google.cloud import storage
import os

# Credential Setup (Same as pipeline)
CREDENTIALS_DIR = r"D:\work\GOOGLE_APPLICATION_CREDENTIALS"
CREDENTIALS_FILE = "helpful-girder-421422-ee6bb27e5b9a.json"
CREDENTIALS_PATH = os.path.join(CREDENTIALS_DIR, CREDENTIALS_FILE)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

# Configuration
PROJECT_ID = "helpful-girder-421422"
BUCKET_NAME = "trade-mlops-bucket"
SOURCE_FILE = "data/stock.csv"
DESTINATION_BLOB = "data/stock.csv"

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    print(f"Uploading {source_file_name} to gs://{bucket_name}/{destination_blob_name}...")
    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

if __name__ == "__main__":
    if not os.path.exists(SOURCE_FILE):
        print(f"Error: Source file {SOURCE_FILE} not found.")
    else:
        try:
            upload_blob(BUCKET_NAME, SOURCE_FILE, DESTINATION_BLOB)
        except Exception as e:
            print(f"Failed to upload: {e}")
            print("Please ensure you have authenticated with 'gcloud auth application-default login' if running locally.")
