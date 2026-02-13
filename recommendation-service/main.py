from fastapi import FastAPI, HTTPException
import httpx
import os
import pybreaker

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


# -----------------------------
# Protected Dependency Calls
# -----------------------------

def get_user_preferences(user_id: str):
    @user_profile_cb
    def call_user_service():
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(f"{USER_PROFILE_URL}/users/{user_id}")
            response.raise_for_status()
            return response.json()
    return call_user_service()


def get_movies():
    @content_cb
    def call_content_service():
        with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
            response = client.get(f"{CONTENT_URL}/movies")
            response.raise_for_status()
            return response.json()
    return call_content_service()


def get_trending_movies():
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        response = client.get(f"{TRENDING_URL}/trending")
        response.raise_for_status()
        return response.json()


# -----------------------------
# Main Recommendations Endpoint
# -----------------------------

@app.get("/recommendations/{user_id}")
def get_recommendations(user_id: str):

    fallback_services = []

    # Try user-profile service
    try:
        user_data = get_user_preferences(user_id)
    except pybreaker.CircuitBreakerError:
        fallback_services.append("user-profile-service")
        user_data = {
            "userId": user_id,
            "preferences": ["Comedy", "Family"]  # default fallback
        }
    except Exception:
        raise HTTPException(status_code=500, detail="User service error")

    # Try content-service
    try:
        movies = get_movies()
    except pybreaker.CircuitBreakerError:
        fallback_services.append("content-service")
        movies = []
    except Exception:
        raise HTTPException(status_code=500, detail="Content service error")

    # If both circuits are OPEN → Final fallback
    if len(fallback_services) == 2:
        trending = get_trending_movies()

        return {
            "message": "Our recommendation service is temporarily degraded. Here are some trending movies.",
            "trending": trending,
            "fallback_triggered_for": ", ".join(fallback_services)
        }

    # Normal or single fallback case
    preferred_genres = user_data["preferences"]

    recommended = [
        movie for movie in movies
        if movie.get("genre") in preferred_genres
    ]

    response = {
        "userPreferences": user_data,
        "recommendations": recommended
    }

    if fallback_services:
        response["fallback_triggered_for"] = ", ".join(fallback_services)

    return response

@app.post("/simulate/{service_name}/{behavior}")
def simulate_dependency(service_name: str, behavior: str):

    if service_name not in ["user-profile", "content"]:
        raise HTTPException(status_code=400, detail="Invalid service name")

    if behavior not in ["normal", "slow", "fail"]:
        raise HTTPException(status_code=400, detail="Invalid behavior")

    target_url = ""

    if service_name == "user-profile":
        target_url = f"{USER_PROFILE_URL}/internal/simulate/{behavior}"
    elif service_name == "content":
        target_url = f"{CONTENT_URL}/internal/simulate/{behavior}"

    try:
        with httpx.Client(timeout=5) as client:
            response = client.post(target_url)
            response.raise_for_status()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to update dependency state")

    return {
        "message": f"{service_name} set to {behavior}"
    }

def get_cb_state(cb: pybreaker.CircuitBreaker):
    state = cb.current_state
    return str(state).split('.')[-1]  # CLEAN STATE NAME

@app.get("/metrics/circuit-breakers")
def circuit_breaker_metrics():
    return {
        "userProfileCircuitBreaker": {
            "state": get_cb_state(user_profile_cb),
            "failCounter": user_profile_cb.fail_counter,
            "successCounter": user_profile_cb._success_counter
        },
        "contentCircuitBreaker": {
            "state": get_cb_state(content_cb),
            "failCounter": content_cb.fail_counter,
            "successCounter": content_cb._success_counter
        }
    }
