from fastapi import FastAPI
import os

app = FastAPI()

USER_PROFILE_URL = os.getenv("USER_PROFILE_URL")
CONTENT_URL = os.getenv("CONTENT_URL")
TRENDING_URL = os.getenv("TRENDING_URL")

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/")
def root():
    return {
        "message": "Recommendation Service Running",
        "dependencies": {
            "user_profile": USER_PROFILE_URL,
            "content": CONTENT_URL,
            "trending": TRENDING_URL
        }
    }
