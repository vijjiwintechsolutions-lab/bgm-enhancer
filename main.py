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
    if os.path.exists(path):
        os.remove(path)

# Accept both /upload-audio and /upload-audio/ to avoid route issues
@app.post("/upload-audio")
@app.post("/upload-audio/")
async def upload_audio(
    file: UploadFile = File(...),
    volume_gain: float = Query(None, gt=0),
    bass_gain: float = Query(None),
    treble_gain: float = Query(None),
    background_tasks: BackgroundTasks = None
):
    ext = Path(file.filename).suffix.lower()
    if ext not in [".mp3", ".wav", ".m4a", ".ogg"]:
        return {"status": "error", "details": "Unsupported audio format"}

    input_filename = f"temp_{uuid4()}{ext}"
    output_filename = f"enhanced_{uuid4()}{ext}"

    try:
        with open(input_filename, "wb") as f:
            f.write(await file.read())

        filters = []
        if bass_gain is not None:
            filters.append(f"bass=g={bass_gain}")
        if treble_gain is not None:
            filters.append(f"treble=g={treble_gain}")
        if volume_gain is not None:
            filters.append(f"volume={volume_gain}")

        ffmpeg_filter = ",".join(filters) if filters else "bass=g=10,volume=1.5"

        command = [
            "ffmpeg", "-i", input_filename,
            "-af", ffmpeg_filter,
            output_filename
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            error_message = result.stderr.decode()
            return {"status": "error", "details": f"FFmpeg failed:\n{error_message}"}

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
