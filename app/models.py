from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db


def utc_now():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    village = db.Column(db.String(120), nullable=False)
    district = db.Column(db.String(120), nullable=False)
    language = db.Column(db.String(20), default="en", nullable=False)
    score = db.Column(db.Integer, default=0, nullable=False)
    xp_points = db.Column(db.Integer, default=0, nullable=False)
    challenge_streak = db.Column(db.Integer, default=0, nullable=False)
    last_challenge_date = db.Column(db.Date, nullable=True)
    role = db.Column(db.String(30), default="citizen", nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)

    quiz_results = db.relationship("QuizResult", backref="user", lazy=True)
    question_history = db.relationship("UserQuestionHistory", backref="user", lazy=True)
    chats = db.relationship("ChatHistory", backref="user", lazy=True)
    achievements = db.relationship("UserAchievement", backref="user", lazy=True)
    learning_progress = db.relationship("LearningProgress", backref="user", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_volunteer(self):
        return self.role in {"admin", "volunteer"}


class QuizQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    difficulty = db.Column(db.String(30), default="Beginner", nullable=False, index=True)

    attempts = db.relationship("UserQuestionHistory", backref="question", lazy=True)


class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class UserQuestionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("quiz_question.id"), nullable=False, index=True)
    attempted_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class ScamReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    message = db.Column(db.Text, nullable=False)
    risk_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    analysis = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class AwarenessArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    language = db.Column(db.String(20), default="en", nullable=False)
    content = db.Column(db.Text, nullable=False)


class ChatHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class ScamAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(80), nullable=False, index=True)
    severity = db.Column(db.String(20), default="Medium", nullable=False)
    language = db.Column(db.String(20), default="en", nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(80), unique=True, nullable=False)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    xp_reward = db.Column(db.Integer, default=0, nullable=False)


class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    achievement_id = db.Column(db.Integer, db.ForeignKey("achievement.id"), nullable=False, index=True)
    earned_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    achievement = db.relationship("Achievement")


class DailyChallenge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    challenge_date = db.Column(db.Date, unique=True, nullable=False, index=True)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text, nullable=False)


class DailyChallengeAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    challenge_id = db.Column(db.Integer, db.ForeignKey("daily_challenge.id"), nullable=False, index=True)
    selected_answer = db.Column(db.String(1), nullable=False)
    is_correct = db.Column(db.Boolean, default=False, nullable=False)
    attempted_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
    challenge = db.relationship("DailyChallenge")


class LearningProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    level = db.Column(db.String(30), nullable=False, index=True)
    completion_percent = db.Column(db.Integer, default=0, nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)


class FraudIncident(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    fraud_type = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text, nullable=False)
    contact = db.Column(db.String(120), nullable=True)
    screenshot_name = db.Column(db.String(255), nullable=True)
    guidance = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utc_now, nullable=False)
