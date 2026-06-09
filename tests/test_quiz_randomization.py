from app import db
from app.models import QuizQuestion, QuizResult, User, UserQuestionHistory
from app.routes import select_quiz_questions


def register(client, email="random@example.com"):
    return client.post(
        "/register",
        data={
            "full_name": "Random Quiz User",
            "email": email,
            "village": "Rampur",
            "district": "Patna",
            "language": "en",
            "password": "StrongPass@123",
            "confirm_password": "StrongPass@123",
        },
        follow_redirects=True,
    )


def submit_current_quiz(client, app):
    with client.session_transaction() as sess:
        question_ids = list(sess["quiz_question_ids"])
    with app.app_context():
        questions = QuizQuestion.query.filter(QuizQuestion.id.in_(question_ids)).all()
        answers = {f"q{question.id}": question.correct_answer for question in questions}
    return client.post("/quiz", data=answers, follow_redirects=True), question_ids


def test_quiz_get_stores_ten_random_questions_in_session(client):
    register(client)
    response = client.get("/quiz")
    assert response.status_code == 200
    with client.session_transaction() as sess:
        first_ids = list(sess["quiz_question_ids"])

    assert len(first_ids) == 10
    assert len(set(first_ids)) == 10

    orders = {tuple(first_ids)}
    for _ in range(4):
        client.get("/quiz")
        with client.session_transaction() as sess:
            orders.add(tuple(sess["quiz_question_ids"]))
    assert len(orders) > 1


def test_quiz_submission_saves_result_and_question_history(client, app):
    register(client, email="history@example.com")
    client.get("/quiz")
    response, question_ids = submit_current_quiz(client, app)
    assert response.status_code == 200
    assert b"Total Quizzes Attempted" in response.data

    with app.app_context():
        user = User.query.filter_by(email="history@example.com").first()
        assert QuizResult.query.filter_by(user_id=user.id).count() == 1
        stored_ids = {
            row.question_id
            for row in UserQuestionHistory.query.filter_by(user_id=user.id).all()
        }
        assert stored_ids == set(question_ids)


def test_twenty_quiz_attempts_randomize_and_store_history(client, app):
    register(client, email="twenty@example.com")
    attempts = []

    for _ in range(20):
        client.get("/quiz")
        _response, question_ids = submit_current_quiz(client, app)
        attempts.append(question_ids)

    with app.app_context():
        user = User.query.filter_by(email="twenty@example.com").first()
        assert QuizResult.query.filter_by(user_id=user.id).count() == 20
        assert UserQuestionHistory.query.filter_by(user_id=user.id).count() == 200

    assert all(len(question_ids) == 10 for question_ids in attempts)
    assert all(len(set(question_ids)) == 10 for question_ids in attempts)
    assert len({tuple(question_ids) for question_ids in attempts}) == 20
    assert len({frozenset(question_ids) for question_ids in attempts}) > 1


def test_previously_attempted_questions_are_avoided_when_possible(client, app):
    register(client, email="avoid@example.com")
    client.get("/quiz")
    _response, first_ids = submit_current_quiz(client, app)

    client.get("/quiz")
    with client.session_transaction() as sess:
        second_ids = set(sess["quiz_question_ids"])

    assert second_ids.isdisjoint(set(first_ids))


def test_quiz_filters_by_category_and_difficulty(client, app):
    register(client, email="filter@example.com")
    response = client.get("/quiz?category=UPI+Safety&difficulty=Beginner")
    assert response.status_code == 200
    with client.session_transaction() as sess:
        question_ids = list(sess["quiz_question_ids"])

    with app.app_context():
        questions = QuizQuestion.query.filter(QuizQuestion.id.in_(question_ids)).all()
        strict_count = QuizQuestion.query.filter_by(category="UPI Safety", difficulty="Beginner").count()
        selected_strict = [
            question
            for question in questions
            if question.category == "UPI Safety" and question.difficulty == "Beginner"
        ]
        assert len(question_ids) == 10
        assert len(set(question_ids)) == 10
        assert len(selected_strict) == min(strict_count, 10)


def test_select_quiz_questions_falls_back_to_full_pool_when_unused_insufficient(app):
    with app.app_context():
        user = User.query.filter_by(email="admin@cybersuraksha.in").first()
        pool = QuizQuestion.query.limit(10).all()
        for question in pool[:9]:
            db.session.add(UserQuestionHistory(user_id=user.id, question_id=question.id))
        db.session.commit()

        selected = select_quiz_questions(user.id, limit=10)
        assert len(selected) == 10


def test_dashboard_statistics_and_leaderboard_top_10(client, app):
    register(client, email="stats@example.com")
    for _ in range(2):
        client.get("/quiz")
        submit_current_quiz(client, app)

    dashboard = client.get("/dashboard")
    assert b"Total Quizzes Attempted" in dashboard.data
    assert b"Average Score" in dashboard.data
    assert b"Best Score" in dashboard.data
    assert b"Recently Attempted Quizzes" in dashboard.data

    with app.app_context():
        for idx in range(12):
            user = User(
                full_name=f"Leader {idx}",
                email=f"leader{idx}@example.com",
                village="Rampur",
                district="Patna",
                language="en",
                score=idx,
            )
            user.set_password("StrongPass@123")
            db.session.add(user)
        db.session.commit()

    leaderboard = client.get("/leaderboard")
    assert leaderboard.status_code == 200
    assert b"Top 10 Awareness Champions" in leaderboard.data
