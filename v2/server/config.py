import os
from dotenv import load_dotenv
from logger import logger

load_dotenv()

LLM_API_KEY = os.getenv("LLM_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

if not LLM_API_KEY:
    logger.warning("Missing config LLM_API_KEY")
  
if not YOUTUBE_API_KEY:
    logger.warning("Missing config YOUTUBE_API_KEY")
