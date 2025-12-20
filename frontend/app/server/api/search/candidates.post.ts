/**
 * 人才搜索 API - 关键词/语义混合搜索
 */
import prisma from '../../utils/prisma';
import { verifyUserToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    const token = getCookie(event, 'auth_token');
    if (!token) throw createError({ statusCode: 401, message: '请先登录' });

    const payload = await verifyUserToken(token);
    if (!payload) throw createError({ statusCode: 401, message: 'Token 无效' });

    const body = await readBody(event);
    const { query, filters = {} } = body;

    // 简单实现：使用数据库模糊查询
    // TODO: 后续接入向量搜索 (Hybrid Search)

    const where: any = {
        userId: payload.id,
        status: 'active'
    };

    if (query) {
        where.OR = [
            { name: { contains: query, mode: 'insensitive' } },
            { currentTitle: { contains: query, mode: 'insensitive' } },
            { currentCompany: { contains: query, mode: 'insensitive' } },
            { skills: { hasSome: [query] } },
            { resumeText: { contains: query, mode: 'insensitive' } } // 全文搜索
        ];
    }

    // 过滤器
    if (filters.minYears) {
        where.yearsExperience = { gte: filters.minYears };
    }

    const results = await prisma.candidate.findMany({
        where,
        take: 50,
        orderBy: { createdAt: 'desc' }
    });

    return { results };
});
