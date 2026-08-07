import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    MRKT_API_URL = os.getenv("MRKT_API_URL", "https://api.mrkt.io/v1/lots")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///app.db")
    SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", "10"))
    BUDGET_LIMIT = float(os.getenv("BUDGET_LIMIT", "1000.0"))
    MIN_PROFIT = float(os.getenv("MIN_PROFIT", "50.0"))
    MIN_RATING = float(os.getenv("MIN_RATING", "70.0"))
    BLACKLIST_COLLECTIONS = [c.strip() for c in os.getenv("BLACKLIST_COLLECTIONS", "").split(",") if c.strip()]
    MODE = os.getenv("MODE", "analytics")  # test, analytics, semiauto
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
