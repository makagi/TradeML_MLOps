# Hybrid MLOps Trading System

This project implements a Hybrid MLOps architecture for trading systems, allowing for:
1.  **Fast Local Development**: Debug and iterate on model logic locally using `src/train.py`.
2.  **Scalable Cloud Experiments**: Run massive parallel experiments on Vertex AI Pipelines.

## Prerequisites

*   Windows OS
*   Python 3.9+
*   Google Cloud SDK (`gcloud`) installed and authenticated.
*   Google Cloud Project with Vertex AI and GCS enabled.

## Project Structure

*   `src/`: Core logic shared between local and cloud.
    *   `train.py`: The hybrid training script. Trains a model and saves it. Supports local paths and GCS paths.
*   `pipelines/`: Vertex AI Pipeline definitions.
    *   `trading_pipeline.py`: Defines the pipeline, creating a component from `src/train.py` logic, and submits it to Vertex AI.
*   `scripts/`: Helper scripts.
    *   `setup.bat`: Sets up the local virtual environment (`venv`).
    *   `local_run.bat`: Runs `src/train.py` locally with sample data.
    *   `submit_job.bat`: Compiles and submits the pipeline to Vertex AI (triggers `trading_pipeline.py`).
    *   `upload_to_gcs.py`: Uploads local data to GCS.
*   `data/`: Local datasets (ignored by git).
*   `models/`: Local model artifacts (ignored by git).

## Setup

1.  Open a terminal in the project root.
2.  Run the setup script:
    ```cmd
    scripts\setup.bat
    ```

## Workflow

### 1. Local Development (Fast Iteration)

Develop your model logic in `src/train.py`. To test it locally:

```cmd
scripts\local_run.bat
```

This will train a model using `data/stock.csv` and save it to `models/model_local.pkl`.

### 2. Prepare for Cloud (Data Upload)

Before running on the cloud, ensure your data is in Google Cloud Storage:

```cmd
venv\Scripts\python scripts\upload_to_gcs.py
```

*Note: Ensure `scripts\upload_to_gcs.py` is configured with your Bucket Name.*

### 3. Cloud Execution (Parallel Experiments)

To run the pipeline on Vertex AI (which runs `src/train.py` logic in parallel with different configurations):

```cmd
scripts\submit_job.bat
```

This will:
1.  Compile the pipeline.
2.  Submit a job to Vertex AI.
3.  Output a link to the Vertex AI Console to track progress.

## Configuration

*   **Credentials**: Set via `GOOGLE_APPLICATION_CREDENTIALS` in scripts.
*   **Project Config**: defined in `pipelines/trading_pipeline.py` (PROJECT_ID, BUCKET_URI).
