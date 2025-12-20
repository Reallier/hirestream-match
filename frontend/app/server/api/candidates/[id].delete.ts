/**
 * 删除候选人 API
 */
import prisma from '../../utils/prisma';
import { verifyUserToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    const token = getCookie(event, 'auth_token');
    if (!token) throw createError({ statusCode: 401, message: '请先登录' });

    const payload = await verifyUserToken(token);
    if (!payload) throw createError({ statusCode: 401, message: 'Token 无效' });

    const id = getRouterParam(event, 'id');
    if (!id) throw createError({ statusCode: 400, message: 'ID 不能为空' });

    const candidateId = parseInt(id);

    // 验证所有权
    const candidate = await prisma.candidate.findUnique({
        where: { id: candidateId }
    });

    if (!candidate || candidate.userId !== payload.id) {
        throw createError({ statusCode: 404, message: '候选人不存在' });
    }

    // 软删除
    await prisma.candidate.update({
        where: { id: candidateId },
        data: { status: 'deleted' }
    });

    return { success: true };
});
