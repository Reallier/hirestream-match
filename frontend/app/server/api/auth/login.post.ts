/**
 * TalentAI 登录 API
 * 代理到官网认证服务进行用户验证
 */
import prisma from '../../utils/prisma';
import { signSessionToken } from '../../utils/jwt';
import * as bcrypt from 'bcryptjs';

export default defineEventHandler(async (event) => {
    const body = await readBody(event);
    const { username, password } = body;

    if (!username || !password) {
        throw createError({
            statusCode: 400,
            message: '请输入用户名和密码'
        });
    }

    try {
        // 直接从共享数据库查询用户
        const user = await prisma.user.findFirst({
            where: {
                OR: [
                    { username },
                    { email: username }
                ]
            }
        });

        if (!user) {
            throw createError({
                statusCode: 401,
                message: '用户名或密码错误'
            });
        }

        // 验证密码
        const isValid = await bcrypt.compare(password, user.password);
        if (!isValid) {
            throw createError({
                statusCode: 401,
                message: '用户名或密码错误'
            });
        }

        // 生成本地会话 Token
        const token = await signSessionToken({
            id: user.id,
            email: user.email || '',
            name: user.name,
            avatar: user.avatar || undefined
        });

        // 设置 Cookie（跨子域共享）
        const isDev = process.env.NODE_ENV !== 'production';
        setCookie(event, 'auth_token', token, {
            httpOnly: true,
            maxAge: 60 * 60 * 24 * 7, // 7 天
            path: '/',
            ...(isDev ? {} : { domain: '.reallier.top', secure: true }),
            sameSite: 'lax'
        });

        const balance = Number(user.balance);
        const freeQuota = Number(user.freeQuota);

        return {
            success: true,
            user: {
                id: user.id,
                name: user.name,
                email: user.email,
                avatar: user.avatar,
                balance,
                freeQuota,
                totalAvailable: balance + freeQuota,
                role: user.role
            }
        };
    } catch (error: any) {
        console.error('Login error:', error);
        if (error.statusCode) throw error;

        throw createError({
            statusCode: 500,
            message: '登录失败，请稍后重试'
        });
    }
});
