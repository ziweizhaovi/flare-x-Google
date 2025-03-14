import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    # BigQuery Settings
    LIQUIDITY_POOL_QUERY_INTERVAL: int = 60  # seconds
    ALERT_THRESHOLD: float = 0.2  # 20% liquidity drop threshold
    
    # Email Settings
    GMAIL_USER: str = os.getenv('GMAIL_USER', '')
    GMAIL_PASSWORD: str = os.getenv('GMAIL_APP_PASSWORD', '')  # App-specific password
    RECIPIENT_EMAIL: str = os.getenv('RECIPIENT_EMAIL', '')
    
    # Gemini AI Settings
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '') 