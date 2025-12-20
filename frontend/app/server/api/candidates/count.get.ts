/**
 * 获取用户候选人数量
 */
import prisma from '../../utils/prisma';
import { verifyUserToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    const token = getCookie(event, 'auth_token');
    if (!token) {
        return { count: 0 };
    }

    const payload = await verifyUserToken(token);
    if (!payload) {
        return { count: 0 };
    }

    const count = await prisma.candidate.count({
        where: {
            userId: payload.id,
            status: 'active'
        }
    });

    return { count };
});
