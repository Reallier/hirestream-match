/**
 * 更新反馈状态（管理员）
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

    const user = await prisma.user.findUnique({
        where: { id: payload.id },
        select: { role: true }
    });

    if (!user || user.role !== 'admin') {
        throw createError({ statusCode: 403, message: '权限不足' });
    }

    // 获取反馈 ID
    const feedbackId = parseInt(event.context.params?.id || '');
    if (!feedbackId) {
        throw createError({ statusCode: 400, message: '无效的反馈ID' });
    }

    const body = await readBody(event);
    const { status, adminNote } = body;

    // 更新反馈
    const feedback = await prisma.feedback.update({
        where: { id: feedbackId },
        data: {
            status: status || undefined,
            adminNote: adminNote !== undefined ? adminNote : undefined
        }
    });

    return {
        success: true,
        data: feedback
    };
});
