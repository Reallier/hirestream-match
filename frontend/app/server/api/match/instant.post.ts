/**
 * 即时匹配 API
 * 调用后端 API 进行简历匹配，并记录使用量
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

    // 4. 解析请求体
    const formData = await readMultipartFormData(event);
    if (!formData) {
        throw createError({ statusCode: 400, message: '请求格式错误' });
    }

    let jdText = '';
    let resumeText = '';
    let resumeFile: { data: Buffer; filename?: string; type?: string } | null = null;

    for (const item of formData) {
        if (item.name === 'jd') {
            jdText = item.data.toString();
        } else if (item.name === 'resume_text') {
            resumeText = item.data.toString();
        } else if (item.name === 'resume') {
            resumeFile = {
                data: item.data,
                filename: item.filename,
                type: item.type
            };
        }
    }

    if (!jdText) {
        throw createError({ statusCode: 400, message: '请输入职位描述' });
    }

    if (!resumeText && !resumeFile) {
        throw createError({ statusCode: 400, message: '请上传简历或输入简历文本' });
    }

    // 5. 调用后端匹配 API
    const config = useRuntimeConfig();
    const apiBase = config.public.apiBase;

    try {
        const backendFormData = new FormData();
        backendFormData.append('jd', jdText);

        if (resumeText) {
            backendFormData.append('resume_text', resumeText);
        } else if (resumeFile) {
            const blob = new Blob([resumeFile.data], { type: resumeFile.type || 'application/octet-stream' });
            backendFormData.append('resume', blob, resumeFile.filename || 'resume');
        }

        const response = await fetch(`${apiBase}/api/instant-match`, {
            method: 'POST',
            body: backendFormData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `后端返回错误: ${response.status}`);
        }

        const result = await response.json();

        // 6. 记录使用量并扣费
        const cost = result.token_usage?.cost || 0.01; // 默认最低消费
        const requestId = `match_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        // 记录使用
        await prisma.usageRecord.create({
            data: {
                userId: user.id,
                requestId,
                operation: 'instant_match',
                model: result.token_usage?.model || 'qwen',
                promptTokens: result.token_usage?.prompt_tokens || 0,
                completionTokens: result.token_usage?.completion_tokens || 0,
                cost
            }
        });

        // 扣费逻辑：优先扣免费额度，不足部分扣余额
        let newTotalUsage = totalUsage + cost;
        let newBalance = balance;

        if (cost <= freeRemaining) {
            // 免费额度足够
            newTotalUsage = totalUsage + cost;
        } else {
            // 需要扣余额
            const fromFree = freeRemaining;
            const fromBalance = cost - fromFree;
            newTotalUsage = freeQuota; // 用完免费额度
            newBalance = balance - fromBalance;
        }

        await prisma.user.update({
            where: { id: user.id },
            data: {
                totalUsage: newTotalUsage,
                balance: newBalance
            }
        });

        // 7. 保存匹配记录（如果用户同意）
        if (user.consentDataStorage) {
            await prisma.matchRecord.create({
                data: {
                    userId: user.id,
                    jdText,
                    resumeText: resumeText || '[文件上传]',
                    resumeFilename: resumeFile?.filename,
                    matchScore: result.match_score || 0,
                    reportJson: result,
                    promptTokens: result.token_usage?.prompt_tokens || 0,
                    completionTokens: result.token_usage?.completion_tokens || 0,
                    cost
                }
            });
        }

        return result;

    } catch (error: any) {
        console.error('Instant match failed:', error);
        throw createError({
            statusCode: 500,
            message: error.message || '匹配分析失败'
        });
    }
});
