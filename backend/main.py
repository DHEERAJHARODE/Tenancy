from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import io
import base64
import cloudinary
import cloudinary.uploader
from dotenv import load_dotenv
import os

# -------------------------------------------------
# 🔐 Load environment variables
# -------------------------------------------------
load_dotenv()

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

# -------------------------------------------------
# ⚙️ FastAPI Setup
# -------------------------------------------------
app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "template"

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

# -------------------------------------------------
# 🏠 Home Page
# -------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# -------------------------------------------------
# 📤 Upload documents
# -------------------------------------------------
@app.post("/generate-pdf/", response_class=HTMLResponse)
async def upload_docs(
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
    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
    folder_prefix = f"tenants/{safe_name}"

    def upload_to_cloudinary(uploadfile: UploadFile, public_id: str):
        try:
            result = cloudinary.uploader.upload(
                uploadfile.file,
                folder=folder_prefix,
                public_id=public_id,
                overwrite=True
            )
            print(f"✅ Uploaded {public_id}: {result['secure_url']}")
            return result["secure_url"]
        except Exception as e:
            print(f"❌ Failed to upload {public_id}: {e}")
            return None

    # Upload documents
    aadhaar_front_url = upload_to_cloudinary(aadhaar_front, "aadhaar_front")
    aadhaar_back_url = upload_to_cloudinary(aadhaar_back, "aadhaar_back")
    pan_card_url = upload_to_cloudinary(pan_card, "pan_card")
    signature_url = upload_to_cloudinary(signature, "signature")

    # Upload selfie (base64)
    selfie_data = selfieImage.split(",")[-1]
    selfie_bytes = base64.b64decode(selfie_data)
    selfie_file = io.BytesIO(selfie_bytes)
    selfie_url = None
    try:
        selfie_result = cloudinary.uploader.upload(
            selfie_file,
            folder=folder_prefix,
            public_id="selfie",
            overwrite=True
        )
        selfie_url = selfie_result["secure_url"]
        print(f"✅ Uploaded selfie: {selfie_url}")
    except Exception as e:
        print(f"❌ Failed to upload selfie: {e}")

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

# -------------------------------------------------
# 📤 Upload rendered page as image
# -------------------------------------------------
@app.post("/upload-page-image/")
async def upload_page_image(name: str = Form(...), image: UploadFile = File(...)):
    safe_name = "".join(c for c in name if c.isalnum() or c in (" ", "_")).strip().replace(" ", "_")
    folder_prefix = f"tenants/{safe_name}"

    try:
        result = cloudinary.uploader.upload(
            image.file,
            folder=folder_prefix,
            public_id="agreement_page",
            overwrite=True
        )
        print(f"✅ Uploaded agreement page: {result['secure_url']}")
        return JSONResponse({"url": result["secure_url"]})
    except Exception as e:
        print(f"❌ Failed to upload page image: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)
