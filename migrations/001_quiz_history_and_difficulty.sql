ALTER TABLE quiz_question ADD COLUMN difficulty VARCHAR(30) NOT NULL DEFAULT 'Beginner';

CREATE TABLE IF NOT EXISTS user_question_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    attempted_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (question_id) REFERENCES quiz_question (id)
);

CREATE INDEX IF NOT EXISTS ix_user_question_history_user_id ON user_question_history (user_id);
CREATE INDEX IF NOT EXISTS ix_user_question_history_question_id ON user_question_history (question_id);
