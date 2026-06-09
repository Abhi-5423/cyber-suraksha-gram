# Screenshot OCR and Voice Assistant

## Screenshot Uploads

The scam checker accepts image uploads (`jpg`, `jpeg`, `png`, `webp`, `bmp`). Uploaded screenshots are processed with Pillow and pytesseract, then the extracted text is analyzed by both the rule-based detector and AI classifier.

Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

Install the Tesseract OCR engine separately and add it to PATH. On Windows, install Tesseract and confirm:

```powershell
tesseract --version
```

## Voice Assistant

The chatbot keeps browser speech recognition and speech synthesis support. It now also includes backend voice APIs:

```text
POST /api/voice/transcribe
POST /api/voice/speak
```

`SpeechRecognition` transcribes uploaded audio files. `gTTS` generates MP3 speech from assistant text. These services may require internet access depending on the recognizer or TTS provider.
