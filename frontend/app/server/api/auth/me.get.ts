/**
 * 获取当前用户信息
 */
import prisma from '../../utils/prisma';
import { verifyUserToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    const token = getCookie(event, 'auth_token');

    if (!token) {
        return { success: false, user: null };
    }

    const payload = await verifyUserToken(token);
    if (!payload) {
        return { success: false, user: null };
    }

    const user = await prisma.user.findUnique({
        where: { id: payload.id },
        select: {
            id: true,
            name: true,
            email: true,
            avatar: true,
            balance: true,
            freeQuota: true,
            totalUsage: true
        }
    });

    if (!user) {
        return { success: false, user: null };
    }

    const balance = Number(user.balance);
    const freeQuota = Number(user.freeQuota);
    const totalUsage = Number(user.totalUsage);
    const freeRemaining = Math.max(0, freeQuota - totalUsage);

    return {
        success: true,
        user: {
            id: user.id,
            name: user.name,
            email: user.email,
            avatar: user.avatar,
            balance,
            freeQuota: freeRemaining,
            totalAvailable: balance + freeRemaining
        }
    };
});
