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

def get_user_preferences(user_id: str):
    try:
        @user_profile_cb
        def call_user_service():
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.get(f"{USER_PROFILE_URL}/users/{user_id}")
                response.raise_for_status()
                return response.json()

        return call_user_service()

    except (httpx.RequestError, httpx.HTTPStatusError, pybreaker.CircuitBreakerError):
        raise

def get_movies():
    try:
        @content_cb
        def call_content_service():
            with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
                response = client.get(f"{CONTENT_URL}/movies")
                response.raise_for_status()
                return response.json()

        return call_content_service()

    except (httpx.RequestError, httpx.HTTPStatusError, pybreaker.CircuitBreakerError):
        raise

@app.get("/recommendations/{user_id}")
def get_recommendations(user_id: str):
    try:
        user_data = get_user_preferences(user_id)
        movies = get_movies()

        # Filter movies based on user preferences
        preferred_genres = user_data["preferences"]
        recommended = [
            movie for movie in movies
            if movie["genre"] in preferred_genres
        ]

        return {
            "userPreferences": user_data,
            "recommendations": recommended
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
