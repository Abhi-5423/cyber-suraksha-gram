KNOWLEDGE = {
    "upi": {
        "en": "For UPI safety, never enter your PIN to receive money, verify the receiver name, avoid unknown collect requests, and report fraud at 1930.",
        "hi": "UPI सुरक्षा के लिए पैसा पाने के लिए कभी PIN न डालें, प्राप्तकर्ता का नाम जांचें, अनजान collect request न मानें और धोखाधड़ी पर 1930 पर रिपोर्ट करें.",
    },
    "otp": {
        "en": "OTP is only for you. Banks, police, delivery staff, or government officers never need your OTP.",
        "hi": "OTP केवल आपके लिए है. बैंक, पुलिस, डिलीवरी कर्मचारी या सरकारी अधिकारी को आपका OTP कभी नहीं चाहिए.",
    },
    "qr": {
        "en": "Scanning a QR code is normally for paying money, not receiving it. Stop if someone asks you to scan a QR to get payment.",
        "hi": "QR कोड स्कैन करना आमतौर पर पैसा भेजने के लिए होता है, पाने के लिए नहीं. पैसा पाने के लिए QR स्कैन करने को कहा जाए तो रुकें.",
    },
    "kyc": {
        "en": "Do KYC only inside official apps or branches. Do not install screen sharing apps or open links sent by strangers.",
        "hi": "KYC केवल आधिकारिक ऐप या शाखा में करें. अनजान लिंक न खोलें और screen sharing app इंस्टॉल न करें.",
    },
    "loan": {
        "en": "Fake loan apps misuse contacts and demand fees. Use RBI-regulated lenders and never pay advance processing charges to strangers.",
        "hi": "फर्जी loan apps contacts का दुरुपयोग करते हैं और fees मांगते हैं. RBI-regulated lender चुनें और अजनबी को advance fee न दें.",
    },
    "government": {
        "en": "Check government schemes on official .gov.in websites or local offices. Do not pay to receive benefits.",
        "hi": "सरकारी योजना केवल आधिकारिक .gov.in वेबसाइट या स्थानीय कार्यालय से जांचें. लाभ पाने के लिए पैसे न दें.",
    },
    "emergency": {
        "en": "For financial cyber fraud, call 1930 immediately and file a complaint at cybercrime.gov.in with transaction details.",
        "hi": "वित्तीय cyber fraud में तुरंत 1930 पर कॉल करें और transaction details के साथ cybercrime.gov.in पर शिकायत करें.",
    },
}


def assistant_reply(message, language="en"):
    text = (message or "").lower()
    lang = "hi" if language == "hi" or any("\u0900" <= c <= "\u097f" for c in text) else "en"
    for key, replies in KNOWLEDGE.items():
        if key in text or (key == "emergency" and any(word in text for word in ["help", "fraud", "lost", "पैसा", "मदद"])):
            return replies[lang]
    return (
        "Ask me about UPI, OTP, QR, KYC, loan app fraud, government scheme fraud, or emergency steps."
        if lang == "en"
        else "UPI, OTP, QR, KYC, loan app fraud, सरकारी योजना fraud या emergency steps के बारे में पूछें."
    )
