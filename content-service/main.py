from fastapi import FastAPI, HTTPException
import time

app = FastAPI()

service_state = {
    "behavior": "normal"  # normal | slow | fail
}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/internal/simulate/{behavior}")
def simulate_behavior(behavior: str):
    if behavior not in ["normal", "slow", "fail"]:
        raise HTTPException(status_code=400, detail="Invalid behavior")
    
    service_state["behavior"] = behavior
    return {"message": f"content-service set to {behavior}"}

@app.get("/movies")
def get_movies():
    if service_state["behavior"] == "fail":
        raise HTTPException(status_code=500, detail="Simulated failure")

    if service_state["behavior"] == "slow":
        time.sleep(3)

    return [
        {"movieId": 101, "title": "Inception", "genre": "Sci-Fi"},
        {"movieId": 102, "title": "The Dark Knight", "genre": "Action"},
        {"movieId": 103, "title": "Interstellar", "genre": "Sci-Fi"},
        {"movieId": 104, "title": "Avengers", "genre": "Action"}
    ]
