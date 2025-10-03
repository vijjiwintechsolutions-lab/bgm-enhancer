from fastapi import FastAPI, UploadFile, File
import uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to BGM Enhancer API"}

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    # For now, just return file details (we can add FFmpeg later)
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "status": "File received successfully"
    }

# For local testing (won't be used on Render, since it overrides with $PORT)
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
