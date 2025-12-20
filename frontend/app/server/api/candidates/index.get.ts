/**
 * 获取候选人列表 API
 */
import prisma from '../../utils/prisma';
import { verifyUserToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    const token = getCookie(event, 'auth_token');
    if (!token) {
        throw createError({ statusCode: 401, message: '请先登录' });
    }

    const payload = await verifyUserToken(token);
    if (!payload) {
        throw createError({ statusCode: 401, message: 'Token 无效' });
    }

    const query = getQuery(event);
    const page = Number(query.page) || 1;
    const limit = Number(query.limit) || 10;
    const search = query.search as string;

    const skip = (page - 1) * limit;

    const where: any = {
        userId: payload.id,
        status: 'active'
    };

    if (search) {
        where.OR = [
            { name: { contains: search, mode: 'insensitive' } },
            { currentTitle: { contains: search, mode: 'insensitive' } },
            { currentCompany: { contains: search, mode: 'insensitive' } },
            { skills: { hasSome: [search] } }
        ];
    }

    const [total, candidates] = await Promise.all([
        prisma.candidate.count({ where }),
        prisma.candidate.findMany({
            where,
            orderBy: { createdAt: 'desc' },
            skip,
            take: limit,
            select: {
                id: true,
                name: true,
                currentTitle: true,
                currentCompany: true,
                yearsExperience: true,
                skills: true,
                createdAt: true,
                resumeFilename: true
            }
        })
    ]);

    return {
        list: candidates,
        pagination: {
            page,
            limit,
            total,
            pages: Math.ceil(total / limit)
        }
    };
});
