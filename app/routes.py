import json
import random
from collections import Counter
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, Response, flash, jsonify, redirect, render_template, request, send_file, session, url_for
from flask_login import current_user, login_required, login_user, logout_user
from urllib.parse import urlparse

from . import csrf, db, limiter
from .forms import AlertForm, ArticleForm, ChatForm, DIFFICULTIES, LoginForm, QUIZ_CATEGORIES, QuizQuestionForm, RegisterForm, ReportFraudForm, ScamCheckForm, UserRoleForm
from .models import Achievement, AwarenessArticle, ChatHistory, DailyChallenge, DailyChallengeAttempt, FraudIncident, LearningProgress, QuizQuestion, QuizResult, ScamAlert, ScamReport, User, UserAchievement, UserQuestionHistory
from .security import roles_required, sanitize_html, sanitize_text
from .services.certificate import generate_certificate
from .services.chatbot import assistant_reply
from .services.fraud_detector import analyze_message
from .services.ml_scam_detector import predict_scam
from .services.ocr import extract_text_from_image
from .services.voice import synthesize_speech, transcribe_audio

main_bp = Blueprint("main", __name__)
BASE_DIR = Path(__file__).resolve().parent
TRANSLATIONS_DIR = BASE_DIR.parent / "translations"
SUPPORTED_LANGUAGES = {"en", "hi"}
QUIZ_ATTEMPT_SIZE = 10
LEARNING_LEVELS = ["Beginner", "Intermediate", "Advanced"]


def current_language():
    if current_user.is_authenticated:
        lang = current_user.language
    else:
        lang = session.get("lang")
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def safe_redirect_target():
    next_url = request.args.get("next")
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    referrer = request.referrer
    if not referrer:
        return url_for("main.home")
    parsed = urlparse(referrer)
    if parsed.netloc and parsed.netloc != request.host:
        return url_for("main.home")
    return referrer


def valid_quiz_filter(value, choices):
    allowed = {choice for choice, _label in choices}
    return value if value in allowed else ""


def _quiz_query(category="", difficulty=""):
    query = QuizQuestion.query
    if category:
        query = query.filter(QuizQuestion.category == category)
    if difficulty:
        query = query.filter(QuizQuestion.difficulty == difficulty)
    return query


def _append_unique_questions(target, candidates, seen_ids, limit):
    shuffled = candidates[:]
    random.shuffle(shuffled)
    for question in shuffled:
        if question.id in seen_ids:
            continue
        target.append(question)
        seen_ids.add(question.id)
        if len(target) >= limit:
            break


def select_quiz_questions(user_id, category="", difficulty="", limit=QUIZ_ATTEMPT_SIZE):
    query = _quiz_query(category=category, difficulty=difficulty)

    pool = query.all()
    if not pool:
        pool = QuizQuestion.query.all()

    total_pool = QuizQuestion.query.all()
    if len(total_pool) <= limit:
        selected = total_pool[:]
        random.shuffle(selected)
        return selected

    if len(pool) == limit:
        selected = pool[:]
        random.shuffle(selected)
        return selected

    attempted_ids = {
        row.question_id
        for row in UserQuestionHistory.query.filter_by(user_id=user_id).with_entities(UserQuestionHistory.question_id)
    }
    selected = []
    selected_ids = set()

    strict_unused = [question for question in pool if question.id not in attempted_ids]
    strict_pool = strict_unused if strict_unused else pool
    _append_unique_questions(selected, strict_pool, selected_ids, limit)

    if len(selected) < limit and category:
        category_pool = [
            question
            for question in _quiz_query(category=category).all()
            if question.id not in attempted_ids
        ]
        _append_unique_questions(selected, category_pool, selected_ids, limit)

    if len(selected) < limit and difficulty:
        difficulty_pool = [
            question
            for question in _quiz_query(difficulty=difficulty).all()
            if question.id not in attempted_ids
        ]
        _append_unique_questions(selected, difficulty_pool, selected_ids, limit)

    if len(selected) < limit:
        full_unused = [question for question in total_pool if question.id not in attempted_ids]
        fallback_pool = full_unused if len(full_unused) >= limit - len(selected) else total_pool
        _append_unique_questions(selected, fallback_pool, selected_ids, limit)

    return selected[:limit]


@lru_cache(maxsize=8)
def _load_translation_file(lang):
    path = TRANSLATIONS_DIR / f"{lang}.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _translation_bundle():
    english = _load_translation_file("en")
    active = _load_translation_file(current_language())
    return {**english, **active}


def translate(key, **kwargs):
    value = _translation_bundle().get(key, _load_translation_file("en").get(key, key))
    if kwargs:
        try:
            return value.format(**kwargs)
        except (KeyError, ValueError):
            return value
    return value


def _key_from_label(value):
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def localize_rule_result(result):
    risk_key = _key_from_label(result.get("risk_level", "low"))
    result["risk_level_label"] = translate(f"risk_{risk_key}")
    result["recommendation"] = translate(f"recommendation_{risk_key}")
    for item in result.get("matched_rules", []):
        item["label"] = translate(f"rule_{_key_from_label(item.get('rule'))}")
    return result


def localize_ai_result(result):
    if not result:
        return result
    label_key = _key_from_label(result.get("label", "unknown"))
    result["label_label"] = translate(f"label_{label_key}")
    if not result.get("available"):
        result["recommendation"] = translate("ai_recommendation_missing")
    elif label_key == "fraud":
        result["recommendation"] = translate("ai_recommendation_fraud")
    elif label_key == "safe":
        result["recommendation"] = translate("ai_recommendation_safe")
    return result


def champion_rank(points):
    if points >= 500:
        return "Cyber Guardian"
    if points >= 300:
        return "Cyber Champion"
    if points >= 180:
        return "Cyber Protector"
    if points >= 80:
        return "Aware Citizen"
    return "Beginner"


def award_xp(user, points):
    user.xp_points = (user.xp_points or 0) + points
    user.score = max(user.score or 0, min(100, user.xp_points // 5))


def grant_achievement(user, code):
    achievement = Achievement.query.filter_by(code=code).first()
    if not achievement:
        return
    exists = UserAchievement.query.filter_by(user_id=user.id, achievement_id=achievement.id).first()
    if not exists:
        db.session.add(UserAchievement(user_id=user.id, achievement_id=achievement.id))
        award_xp(user, achievement.xp_reward)


def update_learning_progress(user):
    for level in LEARNING_LEVELS:
        attempts = QuizResult.query.filter_by(user_id=user.id).count()
        completion = min(100, attempts * 20)
        progress = LearningProgress.query.filter_by(user_id=user.id, level=level).first()
        if not progress:
            progress = LearningProgress(user_id=user.id, level=level, completion_percent=completion)
            db.session.add(progress)
        else:
            progress.completion_percent = max(progress.completion_percent, completion)


def recovery_guidance(fraud_type):
    base = {
        "UPI Fraud": "Call 1930 immediately, contact your bank, save UTR number and screenshots, and report on cybercrime.gov.in.",
        "OTP Fraud": "Block affected cards/accounts, change passwords, call the bank from official numbers, and report at 1930.",
        "Fake KYC": "Do not open the link again, uninstall remote access apps, call your bank, and file a cybercrime complaint.",
        "QR Scam": "Save the QR image and payment proof, report the transaction to your bank, and call 1930.",
        "Loan App Fraud": "Revoke app permissions, preserve harassment evidence, report the app, and avoid paying advance fees.",
        "Social Media Fraud": "Report and block the profile, preserve chat/payment proof, and warn contacts if impersonation is involved.",
    }
    return base.get(fraud_type, "Preserve evidence, call 1930, contact your bank, and file a complaint at cybercrime.gov.in.")


@main_bp.app_context_processor
def inject_globals():
    bundle = _translation_bundle()
    return {
        "t": bundle,
        "tr": lambda key, **kwargs: translate(key, **kwargs),
        "active_lang": current_language(),
        "supported_languages": SUPPORTED_LANGUAGES,
    }


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
    today = date.today()
    high_risk = ScamReport.query.filter_by(risk_level="High").count()
    champions = User.query.filter(User.score >= 80).count()
    daily_active = User.query.filter(User.created_at >= today).count() + QuizResult.query.filter(QuizResult.date >= today).count()
    stats = {
        "users": User.query.count(),
        "checks": ScamReport.query.count(),
        "quizzes": QuizResult.query.count(),
        "articles": AwarenessArticle.query.count(),
        "high_risk": high_risk,
        "champions": champions,
        "daily_active": daily_active,
    }
    lang = current_language()
    alerts = ScamAlert.query.filter_by(language=lang, is_active=True).order_by(ScamAlert.created_at.desc()).limit(4).all()
    if not alerts:
        alerts = ScamAlert.query.filter_by(language="en", is_active=True).order_by(ScamAlert.created_at.desc()).limit(4).all()
    return render_template("home.html", stats=stats, alerts=alerts)


@main_bp.route("/about")
def about():
    return render_template("content_page.html", title=translate("about_title"), body=translate("about_body"))


@main_bp.route("/about-cyber-fraud")
def about_cyber_fraud():
    return render_template("content_page.html", title=translate("about_fraud_title"), body=translate("about_fraud_body"))


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
            flash(translate("paste_or_upload_warning"), "warning")
            return render_template("scam_checker.html", form=form, result=result, ai_result=ai_result, ocr_result=ocr_result)
        result = localize_rule_result(analyze_message(message))
        ai_result = localize_ai_result(predict_scam(message))
        report = ScamReport(user_id=current_user.id if current_user.is_authenticated else None, message=message, risk_score=result["risk_score"], risk_level=result["risk_level"], analysis=json.dumps(result))
        db.session.add(report)
        if current_user.is_authenticated:
            award_xp(current_user, 10)
            grant_achievement(current_user, "scam_checker")
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
    category = valid_quiz_filter(request.args.get("category", ""), QUIZ_CATEGORIES)
    difficulty = valid_quiz_filter(request.args.get("difficulty", ""), DIFFICULTIES)
    if request.method == "POST":
        question_ids = session.get("quiz_question_ids", [])
        if not question_ids:
            question_ids = [
                int(key[1:])
                for key in request.form
                if key.startswith("q") and key[1:].isdigit()
            ]
        questions = QuizQuestion.query.filter(QuizQuestion.id.in_(question_ids)).all() if question_ids else []
        question_map = {question.id: question for question in questions}
        ordered_questions = [question_map[question_id] for question_id in question_ids if question_id in question_map]
        if not ordered_questions:
            flash(translate("quiz_expired"), "warning")
            return redirect(url_for("main.quiz"))
        score = 0
        for q in ordered_questions:
            if request.form.get(f"q{q.id}") == q.correct_answer:
                score += 10
        current_user.score = max(current_user.score, score)
        award_xp(current_user, score)
        db.session.add(QuizResult(user_id=current_user.id, score=score))
        for question_id in question_ids:
            db.session.add(UserQuestionHistory(user_id=current_user.id, question_id=question_id))
        grant_achievement(current_user, "first_quiz")
        if current_user.xp_points >= 300:
            grant_achievement(current_user, "guardian")
        update_learning_progress(current_user)
        db.session.commit()
        session.pop("quiz_question_ids", None)
        flash(translate("quiz_completed", score=score), "success")
        return redirect(url_for("main.dashboard"))
    questions = select_quiz_questions(current_user.id, category=category, difficulty=difficulty)
    session["quiz_question_ids"] = [question.id for question in questions]
    return render_template(
        "quiz.html",
        questions=questions,
        categories=QUIZ_CATEGORIES,
        difficulties=DIFFICULTIES,
        selected_category=category,
        selected_difficulty=difficulty,
    )


@main_bp.route("/certificate")
@login_required
def certificate():
    score = current_user.score
    pdf, cert_id = generate_certificate(current_user, score)
    return send_file(pdf, mimetype="application/pdf", as_attachment=True, download_name=f"{cert_id}.pdf")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    all_results = QuizResult.query.filter_by(user_id=current_user.id).order_by(QuizResult.date.desc()).all()
    results = all_results[:5]
    total_quizzes = len(all_results)
    average_score = round(sum(result.score for result in all_results) / total_quizzes, 1) if total_quizzes else 0
    best_score = max((result.score for result in all_results), default=current_user.score)
    chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).limit(5).all()
    risk_checks = ScamReport.query.filter_by(user_id=current_user.id).count()
    achievements = UserAchievement.query.filter_by(user_id=current_user.id).order_by(UserAchievement.earned_at.desc()).all()
    learning = LearningProgress.query.filter_by(user_id=current_user.id).all()
    chart_scores = [result.score for result in reversed(results)]
    rank = champion_rank(current_user.xp_points or 0)
    return render_template(
        "dashboard.html",
        results=results,
        chats=chats,
        total_quizzes=total_quizzes,
        average_score=average_score,
        best_score=best_score,
        risk_checks=risk_checks,
        achievements=achievements,
        learning=learning,
        chart_scores=chart_scores,
        rank=rank,
    )


@main_bp.route("/leaderboard")
def leaderboard():
    users = User.query.order_by(User.score.desc(), User.xp_points.desc(), User.full_name.asc()).limit(10).all()
    return render_template("leaderboard.html", users=users, champion_rank=champion_rank)


@main_bp.route("/alerts")
def alerts():
    lang = current_language()
    items = ScamAlert.query.filter_by(language=lang, is_active=True).order_by(ScamAlert.created_at.desc()).all()
    if not items:
        items = ScamAlert.query.filter_by(language="en", is_active=True).order_by(ScamAlert.created_at.desc()).all()
    trending = Counter(alert.category for alert in items).most_common()
    return render_template("alerts.html", alerts=items, trending=trending)


@main_bp.route("/daily-challenge", methods=["GET", "POST"])
@login_required
def daily_challenge():
    today = date.today()
    challenge = DailyChallenge.query.filter_by(challenge_date=today).first() or DailyChallenge.query.order_by(DailyChallenge.challenge_date.desc()).first()
    existing = DailyChallengeAttempt.query.filter_by(user_id=current_user.id, challenge_id=challenge.id).first() if challenge else None
    result = None
    if request.method == "POST" and challenge and not existing:
        selected = request.form.get("answer", "")
        is_correct = selected == challenge.correct_answer
        db.session.add(DailyChallengeAttempt(user_id=current_user.id, challenge_id=challenge.id, selected_answer=selected, is_correct=is_correct))
        if is_correct:
            if current_user.last_challenge_date == today - timedelta(days=1):
                current_user.challenge_streak += 1
            elif current_user.last_challenge_date != today:
                current_user.challenge_streak = 1
            current_user.last_challenge_date = today
            award_xp(current_user, 25)
            grant_achievement(current_user, "daily_challenge")
        db.session.commit()
        result = is_correct
        existing = DailyChallengeAttempt.query.filter_by(user_id=current_user.id, challenge_id=challenge.id).first()
    return render_template("daily_challenge.html", challenge=challenge, existing=existing, result=result)


@main_bp.route("/qr-safety")
def qr_safety():
    return render_template("qr_safety.html")


@main_bp.route("/stories")
def stories():
    return render_template("stories.html")


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
        fraud_type = sanitize_text(form.fraud_type.data)
        screenshot_name = sanitize_text(getattr(form.screenshot.data, "filename", "") or "")
        guidance = recovery_guidance(fraud_type)
        db.session.add(
            FraudIncident(
                user_id=current_user.id if current_user.is_authenticated else None,
                fraud_type=fraud_type,
                description=sanitize_text(form.message.data),
                contact=sanitize_text(form.contact.data),
                screenshot_name=screenshot_name,
                guidance=guidance,
            )
        )
        db.session.commit()
        prepared = {
            "fraud_type": fraud_type,
            "details": sanitize_text(form.message.data),
            "contact": sanitize_text(form.contact.data),
            "portal": "https://www.cybercrime.gov.in",
            "helpline": "1930",
            "guidance": guidance,
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
            session["lang"] = user.language if user.language in SUPPORTED_LANGUAGES else "en"
            return redirect(url_for("main.dashboard"))
        flash(translate("invalid_email_password"), "danger")
    return render_template("auth.html", form=form, mode="login")


@main_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash(translate("email_registered"), "warning")
        else:
            user = User(full_name=sanitize_text(form.full_name.data), email=email, village=sanitize_text(form.village.data), district=sanitize_text(form.district.data), language=form.language.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            session["lang"] = user.language
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
        flash(translate("article_saved"), "success")
        return redirect(url_for("main.admin_articles"))
    return render_template("admin_articles.html", form=form, articles=AwarenessArticle.query.order_by(AwarenessArticle.id.desc()).all())


@main_bp.route("/admin/alerts", methods=["GET", "POST"])
@roles_required("admin", "volunteer")
def admin_alerts():
    form = AlertForm()
    if form.validate_on_submit():
        db.session.add(
            ScamAlert(
                title=sanitize_text(form.title.data),
                category=form.category.data,
                severity=form.severity.data,
                language=form.language.data,
                content=sanitize_html(form.content.data),
            )
        )
        db.session.commit()
        flash(translate("alert_published"), "success")
        return redirect(url_for("main.admin_alerts"))
    return render_template("admin_alerts.html", form=form, alerts=ScamAlert.query.order_by(ScamAlert.created_at.desc()).all())


@main_bp.route("/admin/quiz", methods=["GET", "POST"])
@roles_required("admin", "volunteer")
def admin_quiz():
    form = QuizQuestionForm()
    if form.validate_on_submit():
        db.session.add(QuizQuestion(question=sanitize_text(form.question.data), option_a=sanitize_text(form.option_a.data), option_b=sanitize_text(form.option_b.data), option_c=sanitize_text(form.option_c.data), option_d=sanitize_text(form.option_d.data), correct_answer=form.correct_answer.data, category=form.category.data, difficulty=form.difficulty.data))
        db.session.commit()
        flash(translate("question_saved"), "success")
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
            flash(translate("invalid_user_selected"), "danger")
            return redirect(url_for("main.admin_users"))
        user = db.session.get(User, user_id)
        form = UserRoleForm(request.form, prefix=str(user_id))
        if user and form.validate():
            if user.id == current_user.id and form.role.data != "admin":
                flash(translate("cannot_remove_admin"), "warning")
                return redirect(url_for("main.admin_users"))
            user.role = form.role.data
            db.session.commit()
            flash(translate("user_role_updated"), "success")
            return redirect(url_for("main.admin_users"))
        flash(translate("role_update_failed"), "danger")
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
        "theme_color": "#03142e",
        "icons": [
            {"src": url_for("static", filename="images/favicon-16x16.png"), "sizes": "16x16", "type": "image/png"},
            {"src": url_for("static", filename="images/favicon-32x32.png"), "sizes": "32x32", "type": "image/png"},
            {"src": url_for("static", filename="images/logo-preview.webp"), "sizes": "512x512", "type": "image/webp"},
        ],
    })


@main_bp.route("/service-worker.js")
def service_worker():
    js = "self.addEventListener('install',e=>self.skipWaiting());self.addEventListener('fetch',()=>{});"
    return Response(js, mimetype="application/javascript")
