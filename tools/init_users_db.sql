-- 用户主库初始化脚本
-- 从 talentai 数据库迁移 users 表结构和数据

-- 创建 users 表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255),
    username VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    name VARCHAR(100),
    avatar VARCHAR(500),
    openid VARCHAR(100),
    unionid VARCHAR(100),
    role VARCHAR(50) DEFAULT 'user',
    balance DECIMAL(10,2) DEFAULT 0,
    free_quota DECIMAL(10,2) DEFAULT 10,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_openid ON users(openid);
