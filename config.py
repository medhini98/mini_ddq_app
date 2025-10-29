import os
from dotenv import load_dotenv
load_dotenv()    # reads .env at project root

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")  # postgres://...
    JWT_SECRET = os.getenv("JWT_SECRET", "devsecret")
    JWT_ALG = "HS256"
    ACCESS_TOKEN_EXPIRE_MIN=60*8  # 8h

settings = Settings()