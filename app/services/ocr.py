from io import BytesIO


def extract_text_from_image(file_storage):
    if not file_storage or not file_storage.filename:
        return {"available": False, "text": "", "error": "No screenshot uploaded."}

    try:
        from PIL import Image
        import pytesseract
    except ImportError:
        return {
            "available": False,
            "text": "",
            "error": "OCR dependencies are not installed. Run python -m pip install -r requirements.txt.",
        }

    try:
        image_bytes = file_storage.read()
        file_storage.seek(0)
        image = Image.open(BytesIO(image_bytes))
        image.verify()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        text = pytesseract.image_to_string(image, lang="eng")
    except pytesseract.TesseractNotFoundError:
        return {
            "available": False,
            "text": "",
            "error": "Tesseract OCR engine is not installed or not on PATH.",
        }
    except Exception as exc:
        return {"available": False, "text": "", "error": f"Could not read screenshot: {exc}"}

    cleaned = " ".join(text.split())
    return {"available": True, "text": cleaned, "error": "" if cleaned else "No readable text found in screenshot."}
