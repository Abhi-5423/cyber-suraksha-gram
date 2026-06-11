from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import EmailField, PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional


LANGUAGES = [("en", "English"), ("hi", "हिन्दी")]
ROLES = [("citizen", "Village Citizen"), ("volunteer", "Awareness Volunteer"), ("admin", "Administrator")]
QUIZ_CATEGORIES = [
    ("UPI Safety", "UPI Safety"),
    ("OTP Fraud", "OTP Fraud"),
    ("Banking Security", "Banking Security"),
    ("Social Media Security", "Social Media Security"),
    ("Mobile Security", "Mobile Security"),
]
DIFFICULTIES = [
    ("Beginner", "Beginner"),
    ("Intermediate", "Intermediate"),
    ("Advanced", "Advanced"),
]
ALERT_CATEGORIES = [
    ("UPI Scam", "UPI Scam"),
    ("Fake KYC", "Fake KYC"),
    ("QR Scam", "QR Scam"),
    ("Loan App", "Loan App"),
    ("Phishing", "Phishing"),
]
ALERT_SEVERITIES = [("Low", "Low"), ("Medium", "Medium"), ("High", "High")]
FRAUD_TYPES = [
    ("UPI Fraud", "UPI Fraud"),
    ("OTP Fraud", "OTP Fraud"),
    ("Fake KYC", "Fake KYC"),
    ("QR Scam", "QR Scam"),
    ("Loan App Fraud", "Loan App Fraud"),
    ("Social Media Fraud", "Social Media Fraud"),
]


class RegisterForm(FlaskForm):
    full_name = StringField("Full name", validators=[DataRequired(), Length(min=2, max=120)])
    email = EmailField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    village = StringField("Village", validators=[DataRequired(), Length(min=2, max=120)])
    district = StringField("District", validators=[DataRequired(), Length(min=2, max=120)])
    language = SelectField("Language", choices=LANGUAGES)
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class ScamCheckForm(FlaskForm):
    message = TextAreaField("Message", validators=[Optional(), Length(max=3000)])
    screenshot = FileField(
        "Upload Screenshot",
        validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "bmp"], "Images only.")],
    )
    submit = SubmitField("Check Risk")


class ChatForm(FlaskForm):
    message = TextAreaField("Ask cyber assistant", validators=[DataRequired(), Length(min=2, max=800)])
    submit = SubmitField("Send")


class ArticleForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    category = StringField("Category", validators=[DataRequired(), Length(max=80)])
    language = SelectField("Language", choices=LANGUAGES)
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=20, max=6000)])
    submit = SubmitField("Save Article")


class AlertForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    category = SelectField("Category", choices=ALERT_CATEGORIES)
    severity = SelectField("Severity", choices=ALERT_SEVERITIES)
    language = SelectField("Language", choices=LANGUAGES)
    content = TextAreaField("Content", validators=[DataRequired(), Length(min=20, max=2500)])
    submit = SubmitField("Publish Alert")


class QuizQuestionForm(FlaskForm):
    question = TextAreaField("Question", validators=[DataRequired(), Length(min=10, max=1000)])
    option_a = StringField("Option A", validators=[DataRequired(), Length(max=255)])
    option_b = StringField("Option B", validators=[DataRequired(), Length(max=255)])
    option_c = StringField("Option C", validators=[DataRequired(), Length(max=255)])
    option_d = StringField("Option D", validators=[DataRequired(), Length(max=255)])
    correct_answer = SelectField("Correct Answer", choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")])
    category = SelectField("Category", choices=QUIZ_CATEGORIES)
    difficulty = SelectField("Difficulty", choices=DIFFICULTIES)
    submit = SubmitField("Save Question")


class UserRoleForm(FlaskForm):
    role = SelectField("Role", choices=ROLES)
    submit = SubmitField("Update Role")


class ReportFraudForm(FlaskForm):
    fraud_type = SelectField("Fraud Type", choices=FRAUD_TYPES)
    message = TextAreaField("Incident details", validators=[DataRequired(), Length(min=20, max=2000)])
    screenshot = FileField(
        "Upload Screenshot",
        validators=[FileAllowed(["jpg", "jpeg", "png", "webp", "bmp"], "Images only.")],
    )
    contact = StringField("Phone or email", validators=[Optional(), Length(max=120)])
    submit = SubmitField("Prepare Report")
