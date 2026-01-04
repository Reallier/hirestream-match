-- 在 talentai 数据库创建测试用户
INSERT INTO users (email, username, password, name, role, balance, free_quota, created_at, updated_at) 
VALUES ('demo@intjtech.cn', 'demo', '$2b$10$BUuXB6gmHWUE6zBR8tkDzuzvdZ/u1/FfyW1TGbjPN/1unytnbY3WS', 'Demo User', 'user', 0, 10, NOW(), NOW())
ON CONFLICT (username) DO NOTHING
RETURNING id, username, name;

-- 查询用户
SELECT id, username, name FROM users WHERE username = 'demo';

-- 更新候选人数据关联到新用户
UPDATE candidates SET user_id = (SELECT id FROM users WHERE username = 'demo') WHERE user_id IN (3, 5);
SELECT COUNT(*) as candidates_for_demo FROM candidates WHERE user_id = (SELECT id FROM users WHERE username = 'demo');
