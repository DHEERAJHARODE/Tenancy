from fastapi import FastAPI, Form, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import shutil
import os
import base64

app = FastAPI()

# बेस डायरेक्टरी और स्टैटिक फोल्डर सेटअप
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATE_DIR = BASE_DIR / "template"

# Static और template फोल्डर mount
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

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
    selfieImage: str = Form(...)  # base64 image string
):
    # नाम से फोल्डर बनाएं (सुरक्षित नाम)
    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
    user_dir = STATIC_DIR / safe_name
    os.makedirs(user_dir, exist_ok=True)

    # फाइल सेव करने की हेल्पर फंक्शन
    def save_uploadfile(uploadfile: UploadFile, destination: Path):
        with destination.open("wb") as buffer:
            shutil.copyfileobj(uploadfile.file, buffer)

    # आधार कार्ड के फाइल सेव करें
    save_uploadfile(aadhaar_front, user_dir / f"aadhaar_front{Path(aadhaar_front.filename).suffix}")
    save_uploadfile(aadhaar_back, user_dir / f"aadhaar_back{Path(aadhaar_back.filename).suffix}")
    # पैन कार्ड की फोटो सेव करें
    save_uploadfile(pan_card, user_dir / f"pan_card{Path(pan_card.filename).suffix}")
    # सिग्नेचर सेव करें
    save_uploadfile(signature, user_dir / f"signature{Path(signature.filename).suffix}")

    # सेल्फी (base64) decode करके सेव करें
    selfie_data = selfieImage.split(",")[-1]  # "data:image/png;base64,...." से सिर्फ base64 वाला हिस्सा लें
    selfie_bytes = base64.b64decode(selfie_data)
    selfie_path = user_dir / "selfie.png"
    with open(selfie_path, "wb") as f:
        f.write(selfie_bytes)

    # सभी फाइलों के URL (वेब एक्सेस के लिए)
    base_url = f"/static/{safe_name}"
    signature_url = f"{base_url}/signature{Path(signature.filename).suffix}"
    aadhaar_front_url = f"{base_url}/aadhaar_front{Path(aadhaar_front.filename).suffix}"
    aadhaar_back_url = f"{base_url}/aadhaar_back{Path(aadhaar_back.filename).suffix}"
    pan_card_url = f"{base_url}/pan_card{Path(pan_card.filename).suffix}"
    selfie_url = f"{base_url}/selfie.png"

    # टेम्पलेट को डेटा भेजें
    return templates.TemplateResponse("contract_display.html", {
        "request": request,
        "name": name,
        "father_name": father_name,
        "address": address,
        "aadhaar": aadhaar,
        "pan": pan,
        "mobile": mobile,
        "signature_url": signature_url,
        "aadhaar_front_url": aadhaar_front_url,
        "aadhaar_back_url": aadhaar_back_url,
        "pan_card_url": pan_card_url,
        "selfie_url": selfie_url
    })
