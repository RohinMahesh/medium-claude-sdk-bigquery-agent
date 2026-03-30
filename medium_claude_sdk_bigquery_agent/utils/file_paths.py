import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECKPOINT_DIR = os.path.join(BASE_DIR, ".claude")
DATASET_ID = "tableau_sample_datasets"
TABLE_ID = "superstore_sales"
BQ_LOCATION = "us-central1"
