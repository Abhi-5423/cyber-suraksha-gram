from io import BytesIO


def transcribe_audio(file_storage, language="en-IN"):
    if not file_storage or not file_storage.filename:
        return {"available": False, "text": "", "error": "No audio uploaded."}

    try:
        import speech_recognition as sr
    except ImportError:
        return {
            "available": False,
            "text": "",
            "error": "SpeechRecognition is not installed. Run python -m pip install -r requirements.txt.",
        }

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(file_storage) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language=language)
    except sr.UnknownValueError:
        return {"available": True, "text": "", "error": "Speech was not clear enough to transcribe."}
    except sr.RequestError as exc:
        return {"available": False, "text": "", "error": f"Speech recognition service error: {exc}"}
    except Exception as exc:
        return {"available": False, "text": "", "error": f"Could not process audio: {exc}"}
    return {"available": True, "text": text, "error": ""}


def synthesize_speech(text, language="en"):
    value = (text or "").strip()
    if len(value) < 1:
        return {"available": False, "audio": None, "error": "Text is required."}

    try:
        from gtts import gTTS
    except ImportError:
        return {
            "available": False,
            "audio": None,
            "error": "gTTS is not installed. Run python -m pip install -r requirements.txt.",
        }

    lang = "hi" if language == "hi" else "en"
    try:
        audio = BytesIO()
        gTTS(text=value, lang=lang).write_to_fp(audio)
        audio.seek(0)
    except Exception as exc:
        return {"available": False, "audio": None, "error": f"Could not synthesize speech: {exc}"}
    return {"available": True, "audio": audio, "error": ""}
