import uvicorn

if __name__ == "__main__":
    print("Starting FastAPI server...")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
