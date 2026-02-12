from fastapi import FastAPI, HTTPException
import time

app = FastAPI()

# Default behavior
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
    return {"message": f"user-profile-service set to {behavior}"}

@app.get("/users/{user_id}")
def get_user(user_id: str):
    if service_state["behavior"] == "fail":
        raise HTTPException(status_code=500, detail="Simulated failure")

    if service_state["behavior"] == "slow":
        time.sleep(3)

    return {
        "userId": user_id,
        "preferences": ["Action", "Sci-Fi"]
    }
