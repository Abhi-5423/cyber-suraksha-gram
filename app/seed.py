from . import db
from .models import AwarenessArticle, QuizQuestion, User

AWARENESS = [
    ("UPI Fraud", "UPI", "Never enter UPI PIN to receive money.\nReal Example: A buyer sends a collect request and says it is payment.\nWarning Signs: collect request, pressure, unknown account.\nSafety Tips: Check receiver name, reject unknown requests, keep app updated.\nRecovery Steps: Call 1930, contact bank, save screenshots."),
    ("OTP Fraud", "OTP", "OTP, PIN and CVV are secret.\nReal Example: Caller says your ATM will be blocked unless you share OTP.\nWarning Signs: urgent caller, bank impersonation, OTP demand.\nSafety Tips: Do not share OTP with anyone.\nRecovery Steps: Block card/account and report immediately."),
    ("KYC Fraud", "KYC", "KYC must be completed only through official channels.\nReal Example: Fake support sends a link and asks for Aadhaar and OTP.\nWarning Signs: account closure threat, remote access app, unknown link.\nSafety Tips: Visit branch or official app.\nRecovery Steps: Uninstall suspicious apps and call bank."),
    ("QR Scam", "QR Scam", "QR codes are usually used to pay money.\nReal Example: Seller asks you to scan QR to receive advance payment.\nWarning Signs: QR to receive money, PIN prompt, hurry.\nSafety Tips: Do not scan unknown QR codes for receiving funds.\nRecovery Steps: Report transaction and preserve QR image."),
    ("Fake Loan App", "Loan App", "Fake loan apps trap users with instant approvals and harassment.\nReal Example: App asks for contacts and processing fee.\nWarning Signs: upfront fee, no RBI lender name, abusive recovery.\nSafety Tips: Borrow only from regulated lenders.\nRecovery Steps: Report app, block access, complain to portal."),
    ("Fake Government Scheme", "Government Scheme", "Fraudsters misuse scheme names to collect fees.\nReal Example: Link promises subsidy after payment.\nWarning Signs: private link, registration fee, guaranteed benefit.\nSafety Tips: Check .gov.in sites or panchayat office.\nRecovery Steps: Save payment proof and call 1930."),
    ("WhatsApp Scam", "WhatsApp", "Unknown messages can spread fraud links and impersonation.\nReal Example: Friend's hacked account asks for urgent money.\nWarning Signs: new number, emergency story, link shortener.\nSafety Tips: Confirm by voice call before sending money.\nRecovery Steps: Report and block the account."),
    ("Social Media Scam", "Social Media", "Fraudsters create fake profiles, jobs and marketplace listings.\nReal Example: Fake page sells phones at huge discount.\nWarning Signs: advance payment, no address, copied images.\nSafety Tips: Use trusted marketplaces and cash on delivery when possible.\nRecovery Steps: Report profile and payment trail."),
]

CATEGORIES = ["UPI", "OTP", "Banking", "Social Media", "Mobile Security", "Passwords", "Digital Payments"]
QUESTION_BANK = [
    ("When receiving money through UPI, what should you do with your PIN?", "Enter it quickly", "Share it with sender", "Never enter PIN to receive money", "Send screenshot", "C", "UPI"),
    ("A stranger asks for OTP to unblock your bank account. What is safest?", "Share OTP", "Share half OTP", "Refuse and call official bank number", "Forward OTP to friend", "C", "OTP"),
    ("Which URL is safer for official cybercrime reporting in India?", "random-help.xyz", "cybercrime.gov.in", "quickrefund.click", "bank-kyc.top", "B", "Banking"),
    ("What should you do before sending money to a new UPI ID?", "Ignore name", "Verify receiver name", "Send test OTP", "Disable SMS", "B", "Digital Payments"),
    ("A QR code is sent to receive payment. What is likely?", "Normal always", "May make you pay", "Improves network", "Updates Aadhaar", "B", "UPI"),
    ("Which password is strongest?", "12345678", "village123", "Ravi@1990", "Long unique passphrase with symbols", "D", "Passwords"),
    ("What is a warning sign of fake loan apps?", "RBI lender details", "Written agreement", "Upfront fee and contact access", "Known bank branch", "C", "Mobile Security"),
    ("If money is lost in cyber fraud, first call:", "1930", "1000", "12345", "Bank ad number", "A", "Banking"),
    ("What should you do with unknown WhatsApp job links?", "Click all", "Pay joining fee", "Verify company independently", "Share Aadhaar", "C", "Social Media"),
    ("KYC should be done through:", "Unknown link", "Remote access app", "Official app or branch", "Social media chat", "C", "Banking"),
]


def _expanded_questions():
    questions = []
    for idx in range(50):
        base = QUESTION_BANK[idx % len(QUESTION_BANK)]
        q, a, b, c, d, correct, category = base
        if idx < len(QUESTION_BANK):
            questions.append(base)
        else:
            questions.append((f"{q} Scenario {idx + 1}", a, b, c, d, correct, CATEGORIES[idx % len(CATEGORIES)] if category not in CATEGORIES else category))
    return questions


def seed_database():
    if not User.query.filter_by(email="admin@cybersuraksha.in").first():
        admin = User(
            full_name="Cyber Suraksha Admin",
            email="admin@cybersuraksha.in",
            village="Demo Village",
            district="Demo District",
            language="en",
            role="admin",
            score=100,
        )
        admin.set_password("Admin@12345")
        db.session.add(admin)

    if AwarenessArticle.query.count() == 0:
        for title, category, content in AWARENESS:
            db.session.add(AwarenessArticle(title=title, category=category, language="en", content=content))
            db.session.add(AwarenessArticle(title=title, category=category, language="hi", content=content))

    if QuizQuestion.query.count() < 50:
        QuizQuestion.query.delete()
        for q, a, b, c, d, correct, category in _expanded_questions():
            db.session.add(QuizQuestion(question=q, option_a=a, option_b=b, option_c=c, option_d=d, correct_answer=correct, category=category))

    db.session.commit()
