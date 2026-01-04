CREATE TABLE IF NOT EXISTS hm_feedbacks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER,
    type VARCHAR(50) DEFAULT 'suggestion',
    content TEXT NOT NULL,
    contact VARCHAR(255),
    page VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    admin_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
