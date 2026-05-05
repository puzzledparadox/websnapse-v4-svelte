from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "WebSnapse v4 Simulation Engine Online"}