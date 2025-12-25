/**
 * 获取反馈列表（管理员）
 */
import prisma from '../../utils/prisma';
import { verifyUserToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    // 验证管理员权限
    const token = getCookie(event, 'auth_token');
    if (!token) {
        throw createError({ statusCode: 401, message: '未登录' });
    }

    const payload = await verifyUserToken(token);
    if (!payload) {
        throw createError({ statusCode: 401, message: '登录已过期' });
    }

    // 检查是否是管理员
    const user = await prisma.user.findUnique({
        where: { id: payload.id },
        select: { role: true }
    });

    if (!user || user.role !== 'admin') {
        throw createError({ statusCode: 403, message: '权限不足' });
    }

    // 获取查询参数
    const query = getQuery(event);
    const status = query.status as string || undefined;
    const page = parseInt(query.page as string) || 1;
    const pageSize = parseInt(query.pageSize as string) || 20;

    // 构建查询条件
    const where: any = {};
    if (status) {
        where.status = status;
    }

    // 查询反馈
    const [feedbacks, total] = await Promise.all([
        prisma.feedback.findMany({
            where,
            orderBy: { createdAt: 'desc' },
            skip: (page - 1) * pageSize,
            take: pageSize
        }),
        prisma.feedback.count({ where })
    ]);

    return {
        success: true,
        data: feedbacks,
        total,
        page,
        pageSize,
        totalPages: Math.ceil(total / pageSize)
    };
});
