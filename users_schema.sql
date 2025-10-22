-- Users table for authentication
CREATE TABLE IF NOT EXISTS users (
    user_id         INT AUTO_INCREMENT PRIMARY KEY,
    person_id       INT UNIQUE,
    username        VARCHAR(50) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    is_admin        TINYINT(1) DEFAULT 0,
    is_active       TINYINT(1) DEFAULT 1,
    reset_token     VARCHAR(255) NULL,
    reset_token_expiry DATETIME NULL,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login      DATETIME NULL,
    CONSTRAINT fk_users_person FOREIGN KEY (person_id) REFERENCES persons(person_id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Add index for faster lookups
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_reset_token ON users(reset_token);

