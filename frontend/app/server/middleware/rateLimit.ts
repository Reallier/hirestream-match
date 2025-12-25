/**
 * API 速率限制中间件
 * 基于用户 ID 或 IP 地址进行限流
 */

interface RateLimitEntry {
    count: number;
    resetTime: number;
}

// 内存存储 (生产环境建议使用 Redis)
const rateLimitStore = new Map<string, RateLimitEntry>();

// 配置
const RATE_LIMIT = 10; // 每分钟最大请求数
const WINDOW_MS = 60 * 1000; // 1 分钟窗口

// 需要限流的 API 路径
const RATE_LIMITED_PATHS = [
    '/api/instant-match',
    '/api/match',
    '/api/candidates/ingest'
];

export default defineEventHandler(async (event) => {
    const path = event.path || '';

    // 只对特定 API 进行限流
    const shouldLimit = RATE_LIMITED_PATHS.some(p => path.startsWith(p));
    if (!shouldLimit) {
        return;
    }

    // 获取用户标识 (优先使用用户 ID，其次使用 IP)
    let identifier = getHeader(event, 'x-forwarded-for') ||
        getHeader(event, 'x-real-ip') ||
        'anonymous';

    // 尝试从 cookie 获取用户 ID
    const token = getCookie(event, 'auth_token');
    if (token) {
        try {
            const { verifyUserToken } = await import('../utils/jwt');
            const payload = await verifyUserToken(token);
            if (payload?.id) {
                identifier = `user:${payload.id}`;
            }
        } catch {
            // 忽略 token 验证错误
        }
    }

    const now = Date.now();
    const key = `ratelimit:${identifier}`;

    let entry = rateLimitStore.get(key);

    // 检查是否需要重置窗口
    if (!entry || now > entry.resetTime) {
        entry = {
            count: 0,
            resetTime: now + WINDOW_MS
        };
    }

    entry.count++;
    rateLimitStore.set(key, entry);

    // 设置响应头
    setHeader(event, 'X-RateLimit-Limit', RATE_LIMIT.toString());
    setHeader(event, 'X-RateLimit-Remaining', Math.max(0, RATE_LIMIT - entry.count).toString());
    setHeader(event, 'X-RateLimit-Reset', entry.resetTime.toString());

    // 超过限制
    if (entry.count > RATE_LIMIT) {
        const retryAfter = Math.ceil((entry.resetTime - now) / 1000);
        setHeader(event, 'Retry-After', retryAfter.toString());

        throw createError({
            statusCode: 429,
            message: `请求过于频繁，请 ${retryAfter} 秒后重试`
        });
    }
});

// 定期清理过期条目 (每 5 分钟)
setInterval(() => {
    const now = Date.now();
    for (const [key, entry] of rateLimitStore.entries()) {
        if (now > entry.resetTime) {
            rateLimitStore.delete(key);
        }
    }
}, 5 * 60 * 1000);
