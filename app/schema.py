from sqlalchemy import inspect, text

from . import db


def ensure_schema():
    inspector = inspect(db.engine)
    if "quiz_question" in inspector.get_table_names():
        columns = {column["name"] for column in inspector.get_columns("quiz_question")}
        if "difficulty" not in columns:
            with db.engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE quiz_question "
                        "ADD COLUMN difficulty VARCHAR(30) NOT NULL DEFAULT 'Beginner'"
                    )
                )
