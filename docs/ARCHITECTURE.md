# Architecture

## Database Schema

User: id, full_name, email, password_hash, village, district, language, score, role, created_at.

QuizQuestion: id, question, option_a, option_b, option_c, option_d, correct_answer, category, difficulty.

QuizResult: id, user_id, score, date.

UserQuestionHistory: id, user_id, question_id, attempted_at.

ScamReport: id, message, risk_score, risk_level, analysis, created_at.

AwarenessArticle: id, title, category, language, content.

ChatHistory: id, user_id, message, response, timestamp.

## API Routes

`GET /` home, `GET /awareness`, `GET|POST /scam-checker`, `POST /api/scam-check`, `POST /api/ai-scam-check`, `GET|POST /quiz`, `GET /certificate`, `GET /dashboard`, `GET /leaderboard`, `GET|POST /chatbot`, `GET /help`, `GET|POST /report-fraud`, `GET|POST /login`, `GET|POST /register`.

Admin: `GET /admin`, `GET|POST /admin/articles`, `GET|POST /admin/quiz`, `GET /admin/reports`, `GET|POST /admin/users`.

## Frontend Pages

Home, about, cyber fraud explainer, awareness cards, scam checker, quiz, dashboard, leaderboard, chatbot, emergency help, fraud reporting, login/register, admin dashboard and admin management pages.

## User Flows

Citizen registers, selects language, learns from awareness cards, checks suspicious messages, takes randomized quizzes with category/difficulty filters, downloads certificate, asks assistant and uses emergency help.

Volunteer logs in, manages awareness articles and quiz questions, reviews scam reports and analytics.

Administrator manages every volunteer capability plus user roles.

## Security Architecture

Authentication uses Flask-Login and Werkzeug password hashes. Forms use Flask-WTF CSRF. Inputs are validated through WTForms and sanitized with Bleach. SQLAlchemy avoids ad hoc SQL. Rate limiting protects scam checker and chatbot. Role checks protect admin routes. Session cookies are HTTP-only with SameSite=Lax. Secrets are loaded from environment variables.
