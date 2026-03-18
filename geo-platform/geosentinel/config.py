import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    TOMTOM_API_KEY = os.getenv("TOMTOM_API_KEY")
    TOR_PROXY = os.getenv("TOR_PROXY", "socks5://tor:9050")
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://ollama:11434")
    DATA_DIR = os.getenv("DATA_DIR", "/app/data")

    @classmethod
    def validate(cls):
        if not cls.TOMTOM_API_KEY:
            raise ValueError("TOMTOM_API_KEY is not set in environment or .env file.")
        
        if not os.path.exists(cls.DATA_DIR):
            os.makedirs(cls.DATA_DIR)

config = Config()
