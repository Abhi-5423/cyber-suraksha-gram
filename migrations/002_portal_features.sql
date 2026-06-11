ALTER TABLE user ADD COLUMN xp_points INTEGER NOT NULL DEFAULT 0;
ALTER TABLE user ADD COLUMN challenge_streak INTEGER NOT NULL DEFAULT 0;
ALTER TABLE user ADD COLUMN last_challenge_date DATE;
ALTER TABLE scam_report ADD COLUMN user_id INTEGER;

CREATE TABLE IF NOT EXISTS scam_alert (
    id INTEGER PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    category VARCHAR(80) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'Medium',
    language VARCHAR(20) NOT NULL DEFAULT 'en',
    content TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS achievement (
    id INTEGER PRIMARY KEY,
    code VARCHAR(80) NOT NULL UNIQUE,
    title VARCHAR(120) NOT NULL,
    description VARCHAR(255) NOT NULL,
    xp_reward INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS user_achievement (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    achievement_id INTEGER NOT NULL,
    earned_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id),
    FOREIGN KEY(achievement_id) REFERENCES achievement(id)
);

CREATE TABLE IF NOT EXISTS daily_challenge (
    id INTEGER PRIMARY KEY,
    challenge_date DATE NOT NULL UNIQUE,
    question TEXT NOT NULL,
    option_a VARCHAR(255) NOT NULL,
    option_b VARCHAR(255) NOT NULL,
    option_c VARCHAR(255) NOT NULL,
    option_d VARCHAR(255) NOT NULL,
    correct_answer VARCHAR(1) NOT NULL,
    explanation TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS daily_challenge_attempt (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    challenge_id INTEGER NOT NULL,
    selected_answer VARCHAR(1) NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT 0,
    attempted_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id),
    FOREIGN KEY(challenge_id) REFERENCES daily_challenge(id)
);

CREATE TABLE IF NOT EXISTS learning_progress (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    level VARCHAR(30) NOT NULL,
    completion_percent INTEGER NOT NULL DEFAULT 0,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id)
);

CREATE TABLE IF NOT EXISTS fraud_incident (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    fraud_type VARCHAR(80) NOT NULL,
    description TEXT NOT NULL,
    contact VARCHAR(120),
    screenshot_name VARCHAR(255),
    guidance TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    FOREIGN KEY(user_id) REFERENCES user(id)
);
