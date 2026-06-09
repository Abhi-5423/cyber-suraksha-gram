import re
from urllib.parse import urlparse

RULES = [
    ("OTP", 25, re.compile(r"\botp\b|one[- ]?time password", re.I)),
    ("Password", 20, re.compile(r"\bpassword\b|passcode|pin", re.I)),
    ("KYC", 20, re.compile(r"\bkyc\b|know your customer", re.I)),
    ("Verify Account", 15, re.compile(r"verify (your )?account|account verification|account blocked", re.I)),
    ("Urgent", 15, re.compile(r"urgent|immediately|within \d+ (minute|hour|day)s?|last chance", re.I)),
    ("Click Link", 20, re.compile(r"click (here|link)|tap (here|link)|open this link", re.I)),
    ("Lottery", 20, re.compile(r"lottery|lucky draw|jackpot", re.I)),
    ("Reward", 15, re.compile(r"reward|cashback|free gift|prize", re.I)),
    ("Loan Approved", 25, re.compile(r"loan approved|instant loan|pre[- ]?approved loan", re.I)),
    ("Government Benefit", 20, re.compile(r"government benefit|pm yojana|sarkari yojana|subsidy", re.I)),
]

KNOWN_SAFE_DOMAINS = {"cybercrime.gov.in", "rbi.org.in", "npci.org.in", "uidai.gov.in", "india.gov.in"}
URL_RE = re.compile(r"(https?://[^\s]+|www\.[^\s]+|[a-z0-9-]+\.(?:com|in|net|org|xyz|top|click|loan)[^\s]*)", re.I)


def _risk_level(score):
    if score >= 60:
        return "High"
    if score >= 30:
        return "Medium"
    return "Low"


def _domain(url):
    candidate = url if url.startswith(("http://", "https://")) else f"https://{url}"
    parsed = urlparse(candidate)
    return parsed.netloc.lower().removeprefix("www.")


def analyze_message(message):
    text = message or ""
    score = 0
    matched_rules = []

    for name, points, pattern in RULES:
        if pattern.search(text):
            score += points
            matched_rules.append({"rule": name, "points": points})

    for raw_url in URL_RE.findall(text):
        domain = _domain(raw_url)
        if domain and domain not in KNOWN_SAFE_DOMAINS:
            score += 25
            matched_rules.append({"rule": "Unknown URL", "points": 25, "value": domain})

    score = min(score, 100)
    risk_level = _risk_level(score)
    if risk_level == "High":
        recommendation = "Do not click, pay, share OTP, or reply. Call 1930 immediately if money was lost."
    elif risk_level == "Medium":
        recommendation = "Verify through the official app, bank branch, or known helpline before taking action."
    else:
        recommendation = "No strong scam signals found, but never share OTP, PIN, password, or remote access."

    return {
        "risk_score": score,
        "risk_level": risk_level,
        "matched_rules": matched_rules,
        "recommendation": recommendation,
    }
