-- 更新 demo 用户密码为 Test123
UPDATE users SET password = '$2b$10$qklDld0haqUnfQfmDKS1KuvJOqpYubDNRcdZ.zDyNi9OubXKaqUFu' WHERE username = 'demo';
SELECT username, length(password) as pwd_len FROM users WHERE username = 'demo';
