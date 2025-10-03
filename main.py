from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import subprocess
import os
from uuid import uuid4

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to BGM Enhancer API"}

@app.post("/upload-audio/")
async def upload_audio(file: UploadFile = File(...)):
    # Generate unique filenames
    input_filename = f"temp_{uuid4()}.mp3"
    output_filename = f"enhanced_{uuid4()}.mp3"

    try:
        # Save uploaded file temporarily
        with open(input_filename, "wb") as f:
            f.write(await file.read())

        # FFmpeg filter: increase volume + bass boost
        command = [
            "ffmpeg", "-i", input_filename,
            "-af", "bass=g=10,volume=1.5",
            output_filename
        ]
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # Return enhanced file as downloadable response
        return FileResponse(
            path=output_filename,
            media_type="audio/mpeg",
            filename=f"enhanced_{file.filename}"
        )

    except Exception as e:
        return {"status": "error", "details": str(e)}

    finally:
        # Cleanup input and output files after sending response
        if os.path.exists(input_filename):
            os.remove(input_filename)
        # Delay deletion of output file a few seconds if needed, or handle via background task
