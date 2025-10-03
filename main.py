from fastapi import FastAPI, UploadFile, File, BackgroundTasks, Query
from fastapi.responses import FileResponse
import subprocess
import os
from uuid import uuid4
from pathlib import Path

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to BGM Enhancer API"}

def remove_file(path: str):
    """Helper function to delete a file if it exists."""
    if os.path.exists(path):
        os.remove(path)

@app.post("/upload-audio/")
async def upload_audio(
    file: UploadFile = File(...),
    volume_gain: float = Query(None, gt=0, description="Volume multiplier, e.g., 1.5 for +50%"),
    bass_gain: float = Query(None, description="Bass gain in dB, e.g., 10"),
    treble_gain: float = Query(None, description="Treble gain in dB, e.g., 5"),
    background_tasks: BackgroundTasks = None
):
    # Extract original file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in [".mp3", ".wav", ".m4a", ".ogg"]:
        return {"status": "error", "details": "Unsupported audio format"}

    # Generate unique filenames
    input_filename = f"temp_{uuid4()}{ext}"
    output_filename = f"enhanced_{uuid4()}{ext}"

    try:
        # Save uploaded file temporarily
        with open(input_filename, "wb") as f:
            f.write(await file.read())

        # Build FFmpeg filter dynamically
        filters = []
        if bass_gain is not None:
            filters.append(f"bass=g={bass_gain}")
        if treble_gain is not None:
            filters.append(f"treble=g={treble_gain}")
        if volume_gain is not None:
            filters.append(f"volume={volume_gain}")

        ffmpeg_filter = ",".join(filters) if filters else "bass=g=10,volume=1.5"

        # Run FFmpeg and capture stdout/stderr
        command = [
            "ffmpeg", "-i", input_filename,
            "-af", ffmpeg_filter,
            output_filename
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            # Return FFmpeg stderr in response
            error_message = result.stderr.decode()
            return {"status": "error", "details": f"FFmpeg failed:\n{error_message}"}

        # Schedule deletion after response
        background_tasks.add_task(remove_file, input_filename)
        background_tasks.add_task(remove_file, output_filename)

        return FileResponse(
            path=output_filename,
            media_type=f"audio/{ext.replace('.', '')}",
            filename=f"enhanced_{file.filename}"
        )

    except Exception as e:
        remove_file(input_filename)
        remove_file(output_filename)
        return {"status": "error", "details": str(e)}
