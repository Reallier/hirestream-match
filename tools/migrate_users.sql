-- 从 talentai 数据库迁移用户数据到 intjtech_users
INSERT INTO users (id, email, username, password, name, avatar, openid, unionid, role, balance, free_quota, created_at, updated_at)
SELECT id, email, username, password, name, avatar, openid, unionid, role, balance, free_quota, created_at, updated_at
FROM talentai.users
ON CONFLICT (username) DO NOTHING;

-- 同步序列
SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1));

-- 验证
SELECT id, username, name FROM users;
