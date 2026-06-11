from sqlalchemy import inspect, text

from . import db


def ensure_schema():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    if "quiz_question" in tables:
        columns = {column["name"] for column in inspector.get_columns("quiz_question")}
        if "difficulty" not in columns:
            with db.engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE quiz_question "
                        "ADD COLUMN difficulty VARCHAR(30) NOT NULL DEFAULT 'Beginner'"
                    )
                )
    if "user" in tables:
        columns = {column["name"] for column in inspector.get_columns("user")}
        additions = {
            "xp_points": "ALTER TABLE user ADD COLUMN xp_points INTEGER NOT NULL DEFAULT 0",
            "challenge_streak": "ALTER TABLE user ADD COLUMN challenge_streak INTEGER NOT NULL DEFAULT 0",
            "last_challenge_date": "ALTER TABLE user ADD COLUMN last_challenge_date DATE",
        }
        with db.engine.begin() as connection:
            for column, statement in additions.items():
                if column not in columns:
                    connection.execute(text(statement))
    if "scam_report" in tables:
        columns = {column["name"] for column in inspector.get_columns("scam_report")}
        if "user_id" not in columns:
            with db.engine.begin() as connection:
                connection.execute(text("ALTER TABLE scam_report ADD COLUMN user_id INTEGER"))
