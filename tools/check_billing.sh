#!/bin/bash
# 查询用户余额和计费日志 - 完整检查

echo "==============================================="
echo "=== 1. 查找含 icey 的用户 ==="
echo "==============================================="
docker exec talentai_db psql -U talentai -d talentai -c "SELECT id, email, name, balance, free_quota FROM users WHERE email ILIKE '%icey%';"

echo ""
echo "==============================================="
echo "=== 2. 所有用户列表 (最近创建) ==="
echo "==============================================="
docker exec talentai_db psql -U talentai -d talentai -c "SELECT id, email, name, balance, free_quota, created_at FROM users ORDER BY created_at DESC LIMIT 10;"

echo ""
echo "==============================================="
echo "=== 3. 所有余额调整记录 (最近 20 条) ==="
echo "==============================================="
docker exec talentai_db psql -U talentai -d talentai -c "SELECT ba.*, u.email FROM balance_adjustments ba LEFT JOIN users u ON ba.user_id = u.id ORDER BY ba.created_at DESC LIMIT 20;"

echo ""
echo "==============================================="
echo "=== 4. 后端日志 (最近 3 小时过滤匹配/扣费) ==="
echo "==============================================="
docker logs talentai-backend --since 3h 2>&1 | grep -E 'instant_match|deduct|balance|cost|token|icey' | tail -100
