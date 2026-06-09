import json
from collections import Counter
from pathlib import Path

from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from urllib.parse import urlparse

from . import csrf, db, limiter
from .forms import ArticleForm, ChatForm, LoginForm, QuizQuestionForm, RegisterForm, ReportFraudForm, ScamCheckForm, UserRoleForm
from .models import AwarenessArticle, ChatHistory, QuizQuestion, QuizResult, ScamReport, User
from .security import roles_required, sanitize_html, sanitize_text
from .services.certificate import generate_certificate
from .services.chatbot import assistant_reply
from .services.fraud_detector import analyze_message
from .services.ml_scam_detector import predict_scam
from .services.ocr import extract_text_from_image
from .services.voice import synthesize_speech, transcribe_audio

main_bp = Blueprint("main", __name__)
BASE_DIR = Path(__file__).resolve().parent
SUPPORTED_LANGUAGES = {"en", "hi", "bho", "mai"}


def current_language():
    lang = session.get("lang")
    if not lang and current_user.is_authenticated:
        lang = current_user.language
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def safe_redirect_target():
    referrer = request.referrer
    if not referrer:
        return url_for("main.home")
    parsed = urlparse(referrer)
    if parsed.netloc and parsed.netloc != request.host:
        return url_for("main.home")
    return referrer


def _translations():
    lang = current_language()
    path = BASE_DIR / "translations" / f"{lang}.json"
    if not path.exists():
        path = BASE_DIR / "translations" / "en.json"
    return json.loads(path.read_text(encoding="utf-8"))


@main_bp.app_context_processor
def inject_globals():
    return {"t": _translations(), "active_lang": current_language()}


@main_bp.route("/set-language/<lang>")
def set_language(lang):
    if lang not in SUPPORTED_LANGUAGES:
        lang = "en"
    session["lang"] = lang
    if current_user.is_authenticated:
        current_user.language = lang
        db.session.commit()
    return redirect(safe_redirect_target())


@main_bp.route("/")
def home():
    stats = {
        "users": User.query.count(),
        "checks": ScamReport.query.count(),
        "quizzes": QuizResult.query.count(),
        "articles": AwarenessArticle.query.count(),
    }
    alerts = AwarenessArticle.query.limit(4).all()
    return render_template("home.html", stats=stats, alerts=alerts)


@main_bp.route("/about")
def about():
    return render_template("content_page.html", title="About Cyber Suraksha Gram", body="A rural-first cyber safety platform for learning, checking suspicious messages, reporting incidents, and building village-level awareness.")


@main_bp.route("/about-cyber-fraud")
def about_cyber_fraud():
    return render_template("content_page.html", title="About Cyber Fraud", body="Cyber fraud includes OTP theft, UPI collect scams, fake KYC calls, fake loan apps, social media impersonation, phishing links, and fraudulent government scheme messages.")


@main_bp.route("/awareness")
def awareness():
    lang = current_language()
    articles = AwarenessArticle.query.filter_by(language=lang).all() or AwarenessArticle.query.filter_by(language="en").all()
    return render_template("awareness.html", articles=articles)


@main_bp.route("/scam-checker", methods=["GET", "POST"])
@limiter.limit("20 per hour")
def scam_checker():
    form = ScamCheckForm()
    result = None
    ai_result = None
    ocr_result = None
    if form.validate_on_submit():
        message = sanitize_text(form.message.data)
        if form.screenshot.data:
            ocr_result = extract_text_from_image(form.screenshot.data)
            if ocr_result["text"]:
                message = f"{message} {ocr_result['text']}".strip()
        if len(message) < 3:
            flash("Paste a message or upload a screenshot with readable text.", "warning")
            return render_template("scam_checker.html", form=form, result=result, ai_result=ai_result, ocr_result=ocr_result)
        result = analyze_message(message)
        ai_result = predict_scam(message)
        report = ScamReport(message=message, risk_score=result["risk_score"], risk_level=result["risk_level"], analysis=json.dumps(result))
        db.session.add(report)
        db.session.commit()
    return render_template("scam_checker.html", form=form, result=result, ai_result=ai_result, ocr_result=ocr_result)


@main_bp.route("/api/scam-check", methods=["POST"])
@csrf.exempt
@limiter.limit("30 per hour")
def api_scam_check():
    payload = request.get_json(silent=True) or {}
    message = sanitize_text(payload.get("message", ""))
    if len(message) < 3:
        return jsonify({"error": "message is required"}), 400
    result = analyze_message(message)
    result["ai_analysis"] = predict_scam(message)
    db.session.add(ScamReport(message=message, risk_score=result["risk_score"], risk_level=result["risk_level"], analysis=json.dumps(result)))
    db.session.commit()
    return jsonify(result)


@main_bp.route("/api/ai-scam-check", methods=["POST"])
@csrf.exempt
@limiter.limit("30 per hour")
def api_ai_scam_check():
    payload = request.get_json(silent=True) or {}
    message = sanitize_text(payload.get("message", ""))
    if len(message) < 3:
        return jsonify({"error": "message is required"}), 400
    return jsonify(predict_scam(message, use_transformer=bool(payload.get("use_transformer"))))


@main_bp.route("/api/ocr-scam-check", methods=["POST"])
@csrf.exempt
@limiter.limit("20 per hour")
def api_ocr_scam_check():
    uploaded = request.files.get("screenshot")
    ocr_result = extract_text_from_image(uploaded)
    if not ocr_result["text"]:
        return jsonify({"error": ocr_result["error"] or "No text found.", "ocr": ocr_result}), 400
    rule_result = analyze_message(ocr_result["text"])
    rule_result["ai_analysis"] = predict_scam(ocr_result["text"])
    rule_result["ocr"] = ocr_result
    db.session.add(
        ScamReport(
            message=ocr_result["text"],
            risk_score=rule_result["risk_score"],
            risk_level=rule_result["risk_level"],
            analysis=json.dumps(rule_result),
        )
    )
    db.session.commit()
    return jsonify(rule_result)


@main_bp.route("/api/voice/transcribe", methods=["POST"])
@csrf.exempt
@limiter.limit("20 per hour")
def api_voice_transcribe():
    lang = request.form.get("language", "en-IN")
    result = transcribe_audio(request.files.get("audio"), language=lang)
    status = 200 if result["available"] and result["text"] else 400
    return jsonify(result), status


@main_bp.route("/api/voice/speak", methods=["POST"])
@csrf.exempt
@limiter.limit("30 per hour")
def api_voice_speak():
    payload = request.get_json(silent=True) or {}
    result = synthesize_speech(sanitize_text(payload.get("text", "")), language=current_language())
    if not result["available"]:
        return jsonify({"error": result["error"]}), 400
    return send_file(result["audio"], mimetype="audio/mpeg", download_name="cyber-assistant.mp3")


@main_bp.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():
    questions = QuizQuestion.query.order_by(QuizQuestion.id).limit(10).all()
    if request.method == "POST":
        score = 0
        for q in questions:
            if request.form.get(f"q{q.id}") == q.correct_answer:
                score += 10
        current_user.score = max(current_user.score, score)
        db.session.add(QuizResult(user_id=current_user.id, score=score))
        db.session.commit()
        flash(f"Quiz completed. Score: {score}/100", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("quiz.html", questions=questions)


@main_bp.route("/certificate")
@login_required
def certificate():
    score = current_user.score
    pdf, cert_id = generate_certificate(current_user, score)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name=f"{cert_id}.pdf")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date.desc()).limit(5).all()
    chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(5).all()
    return render_template("dashboard.html", results=results, chats=chats)


@main_bp.route("/leaderboard")
def leaderboard():
    users = User.query.order_by(User.score.desc(), User.full_name.asc()).limit(20).all()
    return render_template("leaderboard.html", users=users)


@main_bp.route("/chatbot", methods=["GET", "POST"])
@limiter.limit("40 per hour")
def chatbot():
    form = ChatForm()
    reply = None
    if form.validate_on_submit():
        message = sanitize_text(form.message.data)
        reply = assistant_reply(message, current_language())
        db.session.add(ChatHistory(user_id=current_user.id if current_user.is_authenticated else None, message=message, response=reply))
        db.session.commit()
    history = []
    if current_user.is_authenticated:
        history = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(8).all()
    return render_template("chatbot.html", form=form, reply=reply, history=history)


@main_bp.route("/help")
def help_page():
    return render_template("help.html")


@main_bp.route("/report-fraud", methods=["GET", "POST"])
def report_fraud():
    form = ReportFraudForm()
    prepared = None
    if form.validate_on_submit():
        prepared = {
            "details": sanitize_text(form.message.data),
            "contact": sanitize_text(form.contact.data),
            "portal": "https://www.cybercrime.gov.in",
            "helpline": "1930",
        }
    return render_template("report_fraud.html", form=form, prepared=prepared)


@main_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for("main.dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("auth.html", form=form, mode="login")


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Email is already registered.", "warning")
        else:
            user = User(full_name=sanitize_text(form.full_name.data), email=email, village=sanitize_text(form.village.data), district=sanitize_text(form.district.data), language=form.language.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for("main.dashboard"))
    return render_template("auth.html", form=form, mode="register")


@main_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.home"))


@main_bp.route("/admin")
@roles_required("admin", "volunteer")
def admin():
    scam_types = Counter()
    for report in ScamReport.query.all():
        try:
            data = json.loads(report.analysis)
        except (TypeError, json.JSONDecodeError):
            continue
        scam_types.update(item["rule"] for item in data.get("matched_rules", []))
    analytics = {
        "users": User.query.count(),
        "reports": ScamReport.query.count(),
        "quizzes": QuizResult.query.count(),
        "articles": AwarenessArticle.query.count(),
        "top_scam_types": scam_types.most_common(5),
    }
    return render_template("admin.html", analytics=analytics)


@main_bp.route("/admin/articles", methods=["GET", "POST"])
@roles_required("admin", "volunteer")
def admin_articles():
    form = ArticleForm()
    if form.validate_on_submit():
        db.session.add(AwarenessArticle(title=sanitize_text(form.title.data), category=sanitize_text(form.category.data), language=form.language.data, content=sanitize_html(form.content.data)))
        db.session.commit()
        flash("Article saved.", "success")
        return redirect(url_for("main.admin_articles"))
    return render_template("admin_articles.html", form=form, articles=AwarenessArticle.query.order_by(AwarenessArticle.id.desc()).all())


@main_bp.route("/admin/quiz", methods=["GET", "POST"])
@roles_required("admin", "volunteer")
def admin_quiz():
    form = QuizQuestionForm()
    if form.validate_on_submit():
        db.session.add(QuizQuestion(question=sanitize_text(form.question.data), option_a=sanitize_text(form.option_a.data), option_b=sanitize_text(form.option_b.data), option_c=sanitize_text(form.option_c.data), option_d=sanitize_text(form.option_d.data), correct_answer=form.correct_answer.data, category=sanitize_text(form.category.data)))
        db.session.commit()
        flash("Question saved.", "success")
        return redirect(url_for("main.admin_quiz"))
    return render_template("admin_quiz.html", form=form, questions=QuizQuestion.query.order_by(QuizQuestion.id.desc()).limit(60).all())


@main_bp.route("/admin/reports")
@roles_required("admin", "volunteer")
def admin_reports():
    return render_template("admin_reports.html", reports=ScamReport.query.order_by(ScamReport.created_at.desc()).all())


@main_bp.route("/admin/users", methods=["GET", "POST"])
@roles_required("admin")
def admin_users():
    if request.method == "POST":
        try:
            user_id = int(request.form.get("user_id", 0))
        except (TypeError, ValueError):
            flash("Invalid user selected.", "danger")
            return redirect(url_for("main.admin_users"))
        user = db.session.get(User, user_id)
        form = UserRoleForm(request.form, prefix=str(user_id))
        if user and form.validate():
            if user.id == current_user.id and form.role.data != "admin":
                flash("You cannot remove your own administrator role.", "warning")
                return redirect(url_for("main.admin_users"))
            user.role = form.role.data
            db.session.commit()
            flash("User role updated.", "success")
            return redirect(url_for("main.admin_users"))
        flash("Could not update user role.", "danger")
        return redirect(url_for("main.admin_users"))
    return render_template("admin_users.html", users=User.query.order_by(User.created_at.desc()).all())


@main_bp.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "Cyber Suraksha Gram",
        "short_name": "SurakshaGram",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#f8fafc",
        "theme_color": "#0f766e",
        "icons": [],
    })


@main_bp.route("/service-worker.js")
def service_worker():
    js = "self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('fetch',()=>{});"
    return Response(js, mimetype="application/javascript")
