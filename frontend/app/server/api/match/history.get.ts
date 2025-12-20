/**
 * 获取匹配历史记录 API
 */
import prisma from '../../utils/prisma';
import { verifyUserToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    const token = getCookie(event, 'auth_token');
    if (!token) throw createError({ statusCode: 401, message: '请先登录' });

    const payload = await verifyUserToken(token);
    if (!payload) throw createError({ statusCode: 401, message: 'Token 无效' });

    const records = await prisma.matchRecord.findMany({
        where: { userId: payload.id },
        orderBy: { createdAt: 'desc' },
        take: 20
    });

    return { records };
});
