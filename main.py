from fastapi import FastAPI, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from temp import CozmoEasy
import uvicorn
import pycozmo

app = FastAPI()
cozmo = CozmoEasy()

class Command(BaseModel):
    command: str

@app.post("/command")
def handle_command(cmd: Command):
    command = cmd.command.strip()
    print(f"📥 Received command: {command}")

    if command.lower().startswith("say "):
        text = command[4:].strip()
        cozmo.say(text)
        return {"status": f"Said: {text}"}

    mapping = {
        "forward": cozmo.go,
        "go": cozmo.go,
        "backward": cozmo.back,
        "back": cozmo.back,
        "turn left": cozmo.left,
        "left": cozmo.left,
        "turn right": cozmo.right,
        "turn": cozmo.turn,
        "right": cozmo.right,
        "stop": lambda: cozmo.cli.drive_wheels(0, 0),
        "bye": cozmo.bye,
        "light on": cozmo.light_on,
        "light off": cozmo.light_off,
        "celebrate": cozmo.celebrate,
        "hand up": cozmo.hand_up,
        "hand down": cozmo.hand_down,
        "head up": cozmo.head_up,
        "head down": cozmo.head_down,
        "happy": cozmo.happy,
        "angry": cozmo.angry,
        "surprised": cozmo.surprised,
        "sad": cozmo.sad,
        "disgusted": cozmo.disgusted,
        "afraid": cozmo.afraid,
        "guilty": cozmo.guilty,
        "disappointed": cozmo.disappointed,
        "embarrassed": cozmo.embarrassed,
        "annoyed": cozmo.annoyed,
        "tired": cozmo.tired,
        "excited": cozmo.excited,
        "amazed": cozmo.amazed,
        "confused": cozmo.confused,
        "bored": cozmo.bored,
        "furious": cozmo.furious,
        "suspicious": cozmo.suspicious,
        "rejected": cozmo.rejected,
    }
    func = mapping.get(command)
    if func:
        func()
        return {"status": f"Ran command: {command}"}
    else:
        return {"status": f"Unknown command: {command}"}

@app.post("/play_audio")
async def play_audio(file: UploadFile):
    import tempfile, shutil, os, subprocess

    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp_in:
        shutil.copyfileobj(file.file, tmp_in)
        input_path = tmp_in.name

    # Convert webm to wav (Cozmo-compatible: 22050Hz, mono, s16)
    output_path = input_path.replace(".webm", ".wav")
    padded_path = input_path.replace(".webm", "_padded.wav")
    silence_path = input_path.replace(".webm", "_silence.wav")

    try:
        # Convert webm to wav
        subprocess.run([
            "ffmpeg", "-y", "-i", input_path,
            "-ar", "22050", "-ac", "1", "-sample_fmt", "s16",
            output_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Create 0.4s silence
        subprocess.run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
            "-t", "0.4", "-q:a", "9", "-acodec", "pcm_s16le", silence_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Concatenate silence + user audio
        subprocess.run([
            "ffmpeg", "-y",
            "-i", silence_path,
            "-i", output_path,
            "-filter_complex", "[0][1]concat=n=2:v=0:a=1[a]",
            "-map", "[a]",
            padded_path
        ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Play on Cozmo
        cozmo.cli.set_volume(50000)
        cozmo.cli.play_audio(padded_path)
        cozmo.cli.wait_for(pycozmo.event.EvtAudioCompleted)

        return {"status": "✅ Cozmo played your recording!"}
    except Exception as e:
        print("❌ Error in play_audio:", e)
        return {"status": f"❌ Error: {e}"}
    finally:
        for f in [input_path, output_path, silence_path, padded_path]:
            try: os.remove(f)
            except: pass


@app.get("/ping")
def ping():
    return {"status": "ok"}

app.mount("/public", StaticFiles(directory="public"), name="public")

@app.get("/")
def serve_frontend():
    return FileResponse("public/index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)

