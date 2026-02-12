from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/trending")
def get_trending():
    return [
        {"movieId": 99, "title": "Trending Movie 1"},
        {"movieId": 100, "title": "Trending Movie 2"}
    ]
