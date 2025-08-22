import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB   = int(os.getenv("REDIS_DB", 0))
CACHE_TTL  = int(os.getenv("CACHE_TTL", 60))
DATASET_PATH = os.getenv("DATASET_PATH", "data/.airline_preprocessed.csv")
