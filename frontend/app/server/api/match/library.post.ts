/**
 * JD 匹配 API - 从用户人才库中匹配
 */
import prisma from '../../utils/prisma';
import { verifyUserToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    // 1. 验证用户
    const token = getCookie(event, 'auth_token');
    if (!token) {
        throw createError({ statusCode: 401, message: '请先登录' });
    }

    const payload = await verifyUserToken(token);
    if (!payload) {
        throw createError({ statusCode: 401, message: 'Token 无效' });
    }

    // 2. 获取用户信息
    const user = await prisma.user.findUnique({
        where: { id: payload.id }
    });

    if (!user) {
        throw createError({ statusCode: 404, message: '用户不存在' });
    }

    // 3. 检查余额
    const balance = Number(user.balance);
    const freeQuota = Number(user.freeQuota);
    const totalUsage = Number(user.totalUsage);
    const freeRemaining = Math.max(0, freeQuota - totalUsage);
    const totalAvailable = balance + freeRemaining;

    if (totalAvailable <= 0) {
        throw createError({ statusCode: 402, message: '余额不足，请充值后使用' });
    }

    // 4. 解析请求
    const body = await readBody(event);
    const { jd, top_k = 10 } = body;

    if (!jd) {
        throw createError({ statusCode: 400, message: '请输入职位描述' });
    }

    // 5. 获取用户的候选人
    const candidates = await prisma.candidate.findMany({
        where: {
            userId: payload.id,
            status: 'active'
        },
        orderBy: { createdAt: 'desc' }
    });

    if (candidates.length === 0) {
        throw createError({ statusCode: 400, message: '您的人才库为空，请先上传简历' });
    }

    // 6. 调用后端进行批量匹配
    const config = useRuntimeConfig();
    const apiBase = config.public.apiBase;

    try {
        const response = await fetch(`${apiBase}/api/batch-match`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jd,
                candidates: candidates.map(c => ({
                    id: c.id,
                    name: c.name,
                    resume_text: c.resumeText,
                    current_title: c.currentTitle,
                    current_company: c.currentCompany,
                    years_experience: c.yearsExperience,
                    skills: c.skills
                })),
                top_k
            })
        });

        if (!response.ok) {
            throw new Error('匹配服务暂时不可用');
        }

        const result = await response.json();

        // 7. 记录使用量（按匹配次数计费）
        const cost = result.token_usage?.cost || 0.05;
        const requestId = `lib_match_${Date.now()}`;

        await prisma.usageRecord.create({
            data: {
                userId: user.id,
                requestId,
                operation: 'library_match',
                model: result.token_usage?.model || 'qwen',
                promptTokens: result.token_usage?.prompt_tokens || 0,
                completionTokens: result.token_usage?.completion_tokens || 0,
                cost
            }
        });

        // 扣费
        let newTotalUsage = totalUsage + cost;
        let newBalance = balance;

        if (cost <= freeRemaining) {
            newTotalUsage = totalUsage + cost;
        } else {
            const fromBalance = cost - freeRemaining;
            newTotalUsage = freeQuota;
            newBalance = balance - fromBalance;
        }

        await prisma.user.update({
            where: { id: user.id },
            data: {
                totalUsage: newTotalUsage,
                balance: newBalance
            }
        });

        return {
            success: true,
            results: result.results || [],
            token_usage: result.token_usage
        };

    } catch (error: any) {
        console.error('Library match failed:', error);
        throw createError({
            statusCode: 500,
            message: error.message || '匹配失败'
        });
    }
});
