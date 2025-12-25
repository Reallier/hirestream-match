/**
 * 提交反馈
 */
import prisma from '../../utils/prisma';
import { verifyUserToken } from '../../utils/jwt';

export default defineEventHandler(async (event) => {
    const body = await readBody(event);
    const { type, content, contact, page } = body;

    if (!content || !content.trim()) {
        throw createError({ statusCode: 400, message: '反馈内容不能为空' });
    }

    // 尝试获取用户信息（可选）
    let userId = null;
    const token = getCookie(event, 'auth_token');
    if (token) {
        const payload = await verifyUserToken(token);
        if (payload) {
            userId = payload.id;
        }
    }

    // 创建反馈记录
    const feedback = await prisma.feedback.create({
        data: {
            userId,
            type: type || 'suggestion',
            content: content.trim(),
            contact: contact?.trim() || null,
            page: page || null,
            status: 'pending'
        }
    });

    return {
        success: true,
        feedbackId: feedback.id,
        message: '感谢您的反馈！我们会认真阅读每一条建议。'
    };
});
