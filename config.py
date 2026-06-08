import os
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("KASTYN_API_URL", "https://api.kastyn.co.uk")
API_TOKEN = os.getenv("KASTYN_API_TOKEN", "")
STATION_ID = os.getenv("KASTYN_STATION_ID", "")
LIBRARY_PATH = os.getenv("KASTYN_LIBRARY_PATH", "")
SUPPORTED_EXTENSIONS = {".mp3", ".flac", ".wav", ".aac", ".ogg", ".m4a"}
SCAN_INTERVAL_MINUTES = int(os.getenv("KASTYN_SCAN_INTERVAL", "60"))
