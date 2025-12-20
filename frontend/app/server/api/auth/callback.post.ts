/**
 * 登录回调 - 处理从官网跳转回来的 token
 */
import prisma from '../../utils/prisma';
import { verifyUserToken, signSessionToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    const body = await readBody(event);
    const { token } = body;

    if (!token) {
        throw createError({ statusCode: 400, message: 'Token is required' });
    }

    // 验证来自官网的 token
    const payload = await verifyUserToken(token);
    if (!payload) {
        throw createError({ statusCode: 401, message: 'Invalid token' });
    }

    // 获取用户信息
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
        throw createError({ statusCode: 404, message: 'User not found' });
    }

    // 签发本地会话 token
    const sessionToken = await signSessionToken({
        id: user.id,
        email: user.email,
        name: user.name,
        avatar: user.avatar || undefined
    });

    // 设置 cookie
    setCookie(event, 'auth_token', sessionToken, {
        httpOnly: true,
        secure: process.env.NODE_ENV === 'production',
        sameSite: 'lax',
        maxAge: 60 * 60 * 24 * 7 // 7 days
    });

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
