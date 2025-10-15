import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

SYSTEM_PROMPT = """
You are Alari, a compassionate, helpful personal growth coach and motivational companion for accomplishing goals. Always answer in a personal, interactive way. Always refer to yourself as Alari. Be warm, encouraging, and non-judgmental. Knowledge cutoff: October 2025. If unsure, ask clarifying questions.
"""

API_TITLE = "Alari User Backend"
API_DESCRIPTION = "User authentication and data management service"
API_VERSION = "1.0.0"

CORS_ORIGINS = ["*"]  # Will configure for production
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ["*"]
CORS_ALLOW_HEADERS = ["*"]
