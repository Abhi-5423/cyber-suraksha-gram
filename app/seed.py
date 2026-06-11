from . import db
from .forms import DIFFICULTIES, QUIZ_CATEGORIES
from datetime import date, timedelta

from .models import Achievement, AwarenessArticle, DailyChallenge, QuizQuestion, ScamAlert, User

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

AWARENESS_HI = {
    "UPI Fraud": (
        "UPI धोखाधड़ी",
        "UPI",
        "पैसा प्राप्त करने के लिए कभी UPI PIN न डालें.\nअसली उदाहरण: खरीदार collect request भेजकर कहता है कि यह payment है.\nचेतावनी संकेत: collect request, दबाव, अनजान account.\nसुरक्षा सुझाव: receiver name जांचें, unknown request reject करें, app updated रखें.\nरिकवरी कदम: 1930 पर कॉल करें, बैंक से संपर्क करें, screenshots संभालें.",
    ),
    "OTP Fraud": (
        "OTP धोखाधड़ी",
        "OTP",
        "OTP, PIN और CVV गुप्त होते हैं.\nअसली उदाहरण: caller कहता है कि आपका ATM block होगा जब तक आप OTP शेयर नहीं करते.\nचेतावनी संकेत: urgent caller, bank impersonation, OTP मांगना.\nसुरक्षा सुझाव: OTP किसी से साझा न करें.\nरिकवरी कदम: card/account block करें और तुरंत report करें.",
    ),
    "KYC Fraud": (
        "KYC धोखाधड़ी",
        "KYC",
        "KYC केवल official channels से पूरा करें.\nअसली उदाहरण: fake support link भेजकर Aadhaar और OTP मांगता है.\nचेतावनी संकेत: account closure threat, remote access app, unknown link.\nसुरक्षा सुझाव: branch या official app का उपयोग करें.\nरिकवरी कदम: suspicious apps uninstall करें और bank को call करें.",
    ),
    "QR Scam": (
        "QR स्कैम",
        "QR Scam",
        "QR codes आमतौर पर पैसा भेजने के लिए उपयोग होते हैं.\nअसली उदाहरण: seller advance payment पाने के लिए QR scan करने को कहता है.\nचेतावनी संकेत: पैसा पाने के लिए QR, PIN prompt, जल्दी करने का दबाव.\nसुरक्षा सुझाव: funds receive करने के लिए unknown QR scan न करें.\nरिकवरी कदम: transaction report करें और QR image संभालें.",
    ),
    "Fake Loan App": (
        "फर्जी लोन ऐप",
        "Loan App",
        "फर्जी loan apps instant approval और harassment से users को फंसाते हैं.\nअसली उदाहरण: app contacts और processing fee मांगता है.\nचेतावनी संकेत: upfront fee, RBI lender name नहीं, abusive recovery.\nसुरक्षा सुझाव: केवल regulated lenders से loan लें.\nरिकवरी कदम: app report करें, access block करें, portal पर complaint करें.",
    ),
    "Fake Government Scheme": (
        "फर्जी सरकारी योजना",
        "Government Scheme",
        "Fraudsters scheme names का गलत उपयोग करके fees वसूलते हैं.\nअसली उदाहरण: link payment के बाद subsidy का वादा करता है.\nचेतावनी संकेत: private link, registration fee, guaranteed benefit.\nसुरक्षा सुझाव: .gov.in sites या panchayat office से जांचें.\nरिकवरी कदम: payment proof संभालें और 1930 पर call करें.",
    ),
    "WhatsApp Scam": (
        "WhatsApp स्कैम",
        "WhatsApp",
        "Unknown messages fraud links और impersonation फैला सकते हैं.\nअसली उदाहरण: दोस्त के hacked account से urgent money मांगा जाता है.\nचेतावनी संकेत: new number, emergency story, link shortener.\nसुरक्षा सुझाव: money भेजने से पहले voice call से confirm करें.\nरिकवरी कदम: account report और block करें.",
    ),
    "Social Media Scam": (
        "सोशल मीडिया स्कैम",
        "Social Media",
        "Fraudsters fake profiles, jobs और marketplace listings बनाते हैं.\nअसली उदाहरण: fake page phones भारी discount पर बेचता है.\nचेतावनी संकेत: advance payment, address नहीं, copied images.\nसुरक्षा सुझाव: trusted marketplaces और संभव हो तो cash on delivery उपयोग करें.\nरिकवरी कदम: profile और payment trail report करें.",
    ),
}

CATEGORIES = [value for value, _label in QUIZ_CATEGORIES]
DIFFICULTY_VALUES = [value for value, _label in DIFFICULTIES]
QUESTION_BANK = [
    ("When receiving money through UPI, what should you do with your PIN?", "Enter it quickly", "Share it with sender", "Never enter PIN to receive money", "Send screenshot", "C", "UPI Safety", "Beginner"),
    ("A stranger asks for OTP to unblock your bank account. What is safest?", "Share OTP", "Share half OTP", "Refuse and call official bank number", "Forward OTP to friend", "C", "OTP Fraud", "Beginner"),
    ("Which URL is safer for official cybercrime reporting in India?", "random-help.xyz", "cybercrime.gov.in", "quickrefund.click", "bank-kyc.top", "B", "Banking Security", "Beginner"),
    ("What should you do before sending money to a new UPI ID?", "Ignore name", "Verify receiver name", "Send test OTP", "Disable SMS", "B", "UPI Safety", "Intermediate"),
    ("A QR code is sent to receive payment. What is likely?", "Normal always", "May make you pay", "Improves network", "Updates Aadhaar", "B", "UPI Safety", "Intermediate"),
    ("Which password is strongest?", "12345678", "village123", "Ravi@1990", "Long unique passphrase with symbols", "D", "Mobile Security", "Beginner"),
    ("What is a warning sign of fake loan apps?", "RBI lender details", "Written agreement", "Upfront fee and contact access", "Known bank branch", "C", "Mobile Security", "Intermediate"),
    ("If money is lost in cyber fraud, first call:", "1930", "1000", "12345", "Bank ad number", "A", "Banking Security", "Beginner"),
    ("What should you do with unknown WhatsApp job links?", "Click all", "Pay joining fee", "Verify company independently", "Share Aadhaar", "C", "Social Media Security", "Intermediate"),
    ("KYC should be done through:", "Unknown link", "Remote access app", "Official app or branch", "Social media chat", "C", "Banking Security", "Advanced"),
]

ALERTS = [
    ("UPI collect request scam rising", "UPI Scam", "High", "en", "Fraudsters are sending collect requests and asking victims to enter UPI PIN to receive money. Reject unknown collect requests and call 1930 after any loss."),
    ("Fake KYC link warning", "Fake KYC", "High", "en", "Messages threatening account closure with unknown KYC links are fraudulent. Complete KYC only in official apps or branches."),
    ("QR code payment trap", "QR Scam", "Medium", "en", "Scanning unknown QR codes can make you pay money. Merchants and citizens should verify receiver names before approving payment."),
    ("UPI collect request scam बढ़ रहा है", "UPI Scam", "High", "hi", "Fraudsters collect request भेजकर पैसा पाने के लिए UPI PIN डालने को कहते हैं. Unknown collect request reject करें और नुकसान हो तो 1930 पर call करें."),
    ("फर्जी KYC link चेतावनी", "Fake KYC", "High", "hi", "Account बंद होने की धमकी देकर unknown KYC link भेजना धोखाधड़ी है. KYC केवल official app या branch में करें."),
    ("QR code payment trap", "QR Scam", "Medium", "hi", "Unknown QR code scan करने से आपका पैसा कट सकता है. Payment approve करने से पहले receiver name verify करें."),
]

ACHIEVEMENTS = [
    ("first_quiz", "First Quiz Completed", "Completed the first cyber awareness quiz.", 50),
    ("scam_checker", "Scam Spotter", "Checked a suspicious message with the scam analyzer.", 25),
    ("daily_challenge", "Daily Defender", "Answered a daily cyber challenge correctly.", 25),
    ("guardian", "Cyber Guardian", "Reached 300 XP through awareness activities.", 100),
]

DAILY_CHALLENGE_BANK = [
    ("What should you do if a caller asks for OTP?", "Share it", "Ignore safety", "Refuse and call official helpline", "Send screenshot", "C", "OTP is secret. No bank or officer needs it."),
    ("What does scanning a QR usually do?", "Receives money", "Pays money", "Blocks fraud", "Updates KYC", "B", "QR scans generally authorize payment, so verify before entering PIN."),
    ("Where should cyber fraud be reported quickly?", "1930 and cybercrime.gov.in", "Random WhatsApp group", "Unknown agent", "Loan app chat", "A", "Early reporting improves chances of freezing fraudulent transactions."),
]


def _expanded_questions():
    questions = []
    for idx in range(50):
        base = QUESTION_BANK[idx % len(QUESTION_BANK)]
        q, a, b, c, d, correct, category, difficulty = base
        if idx < len(QUESTION_BANK):
            questions.append(base)
        else:
            questions.append((f"{q} Scenario {idx + 1}", a, b, c, d, correct, CATEGORIES[idx % len(CATEGORIES)], DIFFICULTY_VALUES[idx % len(DIFFICULTY_VALUES)]))
    return questions


def _normalize_existing_questions():
    category_map = {
        "UPI": "UPI Safety",
        "Digital Payments": "UPI Safety",
        "OTP": "OTP Fraud",
        "Banking": "Banking Security",
        "Social Media": "Social Media Security",
        "Passwords": "Mobile Security",
    }
    for idx, question in enumerate(QuizQuestion.query.order_by(QuizQuestion.id).all()):
        question.category = category_map.get(question.category, question.category)
        if question.category not in CATEGORIES:
            question.category = CATEGORIES[idx % len(CATEGORIES)]
        if not getattr(question, "difficulty", None) or question.difficulty not in DIFFICULTY_VALUES:
            question.difficulty = DIFFICULTY_VALUES[idx % len(DIFFICULTY_VALUES)]


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
            hi_title, hi_category, hi_content = AWARENESS_HI[title]
            db.session.add(AwarenessArticle(title=hi_title, category=hi_category, language="hi", content=hi_content))
    else:
        for title, _category, _content in AWARENESS:
            hi_title, hi_category, hi_content = AWARENESS_HI[title]
            article = AwarenessArticle.query.filter_by(language="hi", category=hi_category).first()
            if article:
                article.title = hi_title
                article.content = hi_content
            elif not AwarenessArticle.query.filter_by(language="hi", title=hi_title).first():
                db.session.add(AwarenessArticle(title=hi_title, category=hi_category, language="hi", content=hi_content))

    if QuizQuestion.query.count() < 50:
        QuizQuestion.query.delete()
        for q, a, b, c, d, correct, category, difficulty in _expanded_questions():
            db.session.add(QuizQuestion(question=q, option_a=a, option_b=b, option_c=c, option_d=d, correct_answer=correct, category=category, difficulty=difficulty))
    else:
        _normalize_existing_questions()

    for title, category, severity, language, content in ALERTS:
        if not ScamAlert.query.filter_by(title=title, language=language).first():
            db.session.add(ScamAlert(title=title, category=category, severity=severity, language=language, content=content))

    for code, title, description, xp_reward in ACHIEVEMENTS:
        if not Achievement.query.filter_by(code=code).first():
            db.session.add(Achievement(code=code, title=title, description=description, xp_reward=xp_reward))

    today = date.today()
    for offset in range(7):
        challenge_date = today + timedelta(days=offset)
        question, a, b, c, d, correct, explanation = DAILY_CHALLENGE_BANK[offset % len(DAILY_CHALLENGE_BANK)]
        if not DailyChallenge.query.filter_by(challenge_date=challenge_date).first():
            db.session.add(
                DailyChallenge(
                    challenge_date=challenge_date,
                    question=question,
                    option_a=a,
                    option_b=b,
                    option_c=c,
                    option_d=d,
                    correct_answer=correct,
                    explanation=explanation,
                )
            )

    db.session.commit()
