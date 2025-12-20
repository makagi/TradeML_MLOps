# Vertex AI Pipeline Execution Guide

This guide walks you through executing your ML pipeline on Vertex AI for the first time.

## Prerequisites

- [x] Virtual environment set up (`scripts\setup_venv.bat`)
- [x] Google Cloud authentication configured
- [x] GCS bucket created: `gs://trade-mlops-bucket`
- [x] Service account with permissions: `akamlops@helpful-girder-421422.iam.gserviceaccount.com`

---

## Quick Start (Automated)

Use the automated setup script:

```cmd
scripts\prepare_vertex_ai.bat
```

This script will:
1. ✓ Generate sample stock data
2. ✓ Upload to GCS
3. ✓ Compile pipeline
4. Ask if you want to submit to Vertex AI

---

## Manual Step-by-Step

### Step 1: Generate Sample Data

Create realistic OHLCV stock data:

```cmd
venv\Scripts\activate
python scripts\generate_sample_data.py 1000 data\stock.csv
```

**Output**: `data/stock.csv` (1000 rows, OHLCV + Target)

### Step 2: Upload to GCS

```cmd
python scripts\upload_to_gcs.py
```

**Verifies**: `gs://trade-mlops-bucket/data/stock.csv`

### Step 3: Configure Pipeline

Edit [`config/pipeline_config.yaml`](file:///d:/work/AI-Trade/TradeML_MLOps/config/pipeline_config.yaml) if needed:

```yaml
# Verify these settings
environment:
  project_id: "helpful-girder-421422"
  bucket: "gs://trade-mlops-bucket"

data:
  raw_data_path: "gs://trade-mlops-bucket/data/stock.csv"
```

### Step 4: Compile Pipeline

```cmd
python run_pipeline.py
```

**Output**: `trading_pipeline.json`

### Step 5: Submit to Vertex AI

When prompted, answer `y`:

```
[SUBMIT?] Submit to Vertex AI? [y/N]: y
```

Or programmatically:

```python
from src.pipeline_builder import PipelineBuilder

builder = PipelineBuilder('config/pipeline_config.yaml')
builder.build_pipeline()
builder.compile('trading_pipeline.json')
builder.submit('trading_pipeline.json')
```

---

## What Happens During Execution

### Pipeline Flow

```
1. Preprocessing (standard_scaler)
   ↓
2. Feature Engineering (technical_indicators)
   ↓ 
3. Parallel Training (4 feature combinations)
   ├─ ["Open", "Close"]
   ├─ ["Open", "Close", "Volume"]
   ├─ ["Open", "High", "Low", "Close", "Volume"]
   └─ ["RSI", "MACD", "SMA_20"]
   ↓
4. Experiment Aggregation
   └─ Selects best model by accuracy
```

### Expected Outputs

**GCS Locations**:
- Models: `gs://trade-mlops-bucket/models/model_*.pkl`
- Metrics: `gs://trade-mlops-bucket/models/model_*_metrics.json`
- Report: `gs://trade-mlops-bucket/reports/experiment_comparison.md`

### Execution Time

- **Preprocessing**: ~1-2 min
- **Feature Engineering**: ~2-3 min
- **Parallel Training**: ~5-10 min (4 jobs in parallel)
- **Aggregation**: ~1 min

**Total**: ~10-15 minutes

---

## Monitoring Execution

### Vertex AI Console

1. Open [Vertex AI Pipelines Console](https://console.cloud.google.com/vertex-ai/pipelines)
2. Select project: `helpful-girder-421422`
3. Find your pipeline: `trading-ml-pipeline`
4. Click to view execution graph

### Check Logs

```python
# In Python
from google.cloud import aiplatform

aiplatform.init(
    project="helpful-girder-421422",
    location="us-central1"
)

# List recent pipeline jobs
jobs = aiplatform.PipelineJob.list()
for job in jobs[:5]:
    print(f"{job.display_name}: {job.state}")
```

### View Results

After completion, check GCS bucket:

```cmd
# Using gsutil (if installed)
gsutil ls gs://trade-mlops-bucket/models/
gsutil cat gs://trade-mlops-bucket/reports/experiment_comparison.md
```

---

## Troubleshooting

### Authentication Error

```
Error: Could not authenticate
```

**Solution**:
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=D:\work\GOOGLE_APPLICATION_CREDENTIALS\helpful-girder-421422-ee6bb27e5b9a.json
gcloud auth application-default login
```

### Permission Denied

```
Error: Permission denied on bucket
```

**Solution**: Ensure service account has roles:
- `roles/storage.objectAdmin`
- `roles/aiplatform.user`

### Data Not Found

```
Error: gs://trade-mlops-bucket/data/stock.csv not found
```

**Solution**:
```cmd
python scripts\upload_to_gcs.py
```

### Pipeline Fails During Execution

Check component logs in Vertex AI Console:
1. Click on failed component
2. View "Logs" tab
3. Check error message

Common issues:
- Missing Python packages → Check `packages_to_install` in component
- Data format mismatch → Verify CSV structure matches expected columns

---

## Next Steps After First Run

### 1. Review Results

```cmd
# Download experiment report
gsutil cp gs://trade-mlops-bucket/reports/experiment_comparison.md reports/
```

### 2. Adjust Configuration

Based on results, modify [`config/pipeline_config.yaml`](file:///d:/work/AI-Trade/TradeML_MLOps/config/pipeline_config.yaml):

```yaml
# Try different feature combinations
experiments:
  feature_combinations:
    - ["RSI", "MACD"]
    - ["SMA_20", "SMA_50", "Volume"]

# Adjust model parameters
components:
  training:
    params:
      n_estimators: 200  # More trees
      max_depth: 15      # Deeper trees
```

### 3. Re-run Pipeline

```cmd
python run_pipeline.py
# Answer 'y' to submit
```

### 4. Compare Experiments

Use Vertex AI Experiments to compare multiple runs:
- Navigate to: Vertex AI → Experiments
- View metrics across runs
- Compare best models from each experiment

---

## Cost Estimation

Approximate costs for 1000 samples (4 parallel jobs):

- **Compute**: ~$0.50-1.00 per run
- **Storage**: Negligible for sample data
- **Pipeline orchestration**: Included in Vertex AI

For production with larger datasets, review [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing).

---

## Advanced: Scheduling Recurring Runs

### Cloud Scheduler Integration

```python
# Create scheduled pipeline (example)
from google.cloud import aiplatform

pipeline = aiplatform.PipelineJob(
    display_name="daily-trading-pipeline",
    template_path="trading_pipeline.json",
    pipeline_root="gs://trade-mlops-bucket/pipeline_root",
    enable_caching=False
)

# Submit with schedule (requires Cloud Scheduler setup)
# See: https://cloud.google.com/vertex-ai/docs/pipelines/schedule-pipeline
```

---

## Support

- **Documentation**: See [README.md](file:///d:/work/AI-Trade/TradeML_MLOps/README.md)
- **System Tests**: Run `python test_system.py`
- **Component Details**: Check `src/components/` directory

---

**Ready to execute?** Run: `scripts\prepare_vertex_ai.bat`
