from fastapi import FastAPI, UploadFile, File
import aiofiles
import uuid
import subprocess
import os
from supabase import create_client

app = FastAPI()

SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"message": "BGM Enhancer API running!"}

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    input_path = f"{UPLOAD_DIR}/{job_id}_{file.filename}"
    output_path = f"{UPLOAD_DIR}/{job_id}.mp3"

    # Save uploaded file
    async with aiofiles.open(input_path, 'wb') as out_file:
        content = await file.read()
        await out_file.write(content)

    # Cut 30 seconds with ffmpeg
    command = [
        "ffmpeg", "-y", "-i", input_path,
        "-t", "30", "-q:a", "0", "-map", "a", output_path
    ]
    subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Upload to Supabase
    with open(output_path, "rb") as f:
        supabase.storage.from_("processed-audio").upload(f"jobs/{job_id}.mp3", f)

    public_url = supabase.storage.from_("processed-audio").get_public_url(f"jobs/{job_id}.mp3")

    # Save job record
    supabase.table("jobs").insert({
        "id": job_id,
        "status": "done",
        "file_url": public_url,
        "quality": "standard"
    }).execute()

    return {"job_id": job_id, "status": "done", "download": public_url}
