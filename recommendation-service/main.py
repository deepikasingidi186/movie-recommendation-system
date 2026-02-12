from fastapi import FastAPI, HTTPException
import httpx
import os
import pybreaker
import time

app = FastAPI()

# Environment variables
USER_PROFILE_URL = os.getenv("USER_PROFILE_URL")
CONTENT_URL = os.getenv("CONTENT_URL")
TRENDING_URL = os.getenv("TRENDING_URL")

REQUEST_TIMEOUT = int(os.getenv("CB_TIMEOUT_SECONDS", 2))
OPEN_DURATION = int(os.getenv("CB_OPEN_DURATION", 30))

# Circuit Breakers
user_profile_cb = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=OPEN_DURATION
)

content_cb = pybreaker.CircuitBreaker(
    fail_max=5,
    reset_timeout=OPEN_DURATION
)

@app.get("/health")
def health():
    return {"status": "healthy"}
