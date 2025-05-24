from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil
import os
import base64

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated_files"  # safer directory for uploads
TEMPLATE_DIR = BASE_DIR / "template"

app.mount("/generated_files", StaticFiles(directory=str(GENERATED_DIR)), name="generated_files")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/generate-pdf/", response_class=HTMLResponse)
async def generate_pdf(
    request: Request,
    name: str = Form(...),
    father_name: str = Form(...),
    address: str = Form(...),
    aadhaar: str = Form(...),
    pan: str = Form(...),
    mobile: str = Form(...),
    signature: UploadFile = File(...),
    aadhaar_front: UploadFile = File(...),
    aadhaar_back: UploadFile = File(...),
    pan_card: UploadFile = File(...),
    selfieImage: str = Form(...)
):
    # Create a safe folder name
    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
    user_dir = GENERATED_DIR / safe_name
    os.makedirs(user_dir, exist_ok=True)

    def save_uploadfile(uploadfile: UploadFile, destination: Path):
        with destination.open("wb") as buffer:
            shutil.copyfileobj(uploadfile.file, buffer)

    save_uploadfile(aadhaar_front, user_dir / f"aadhaar_front{Path(aadhaar_front.filename).suffix}")
    save_uploadfile(aadhaar_back, user_dir / f"aadhaar_back{Path(aadhaar_back.filename).suffix}")
    save_uploadfile(pan_card, user_dir / f"pan_card{Path(pan_card.filename).suffix}")
    save_uploadfile(signature, user_dir / f"signature{Path(signature.filename).suffix}")

    # Save base64 selfie
    selfie_data = selfieImage.split(",")[-1]
    selfie_bytes = base64.b64decode(selfie_data)
    with open(user_dir / "selfie.png", "wb") as f:
        f.write(selfie_bytes)

    # Set file URL path for template
    base_url = f"/generated_files/{safe_name}"
    return templates.TemplateResponse("contract_display.html", {
        "request": request,
        "name": name,
        "father_name": father_name,
        "address": address,
        "aadhaar": aadhaar,
        "pan": pan,
        "mobile": mobile,
        "signature_url": f"{base_url}/signature{Path(signature.filename).suffix}",
        "aadhaar_front_url": f"{base_url}/aadhaar_front{Path(aadhaar_front.filename).suffix}",
        "aadhaar_back_url": f"{base_url}/aadhaar_back{Path(aadhaar_back.filename).suffix}",
        "pan_card_url": f"{base_url}/pan_card{Path(pan_card.filename).suffix}",
        "selfie_url": f"{base_url}/selfie.png"
    })
