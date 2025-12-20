/**
 * 简历上传入库 API
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

    // 2. 解析文件
    const formData = await readMultipartFormData(event);
    if (!formData) {
        throw createError({ statusCode: 400, message: '请上传文件' });
    }

    let file: { data: Buffer; filename?: string; type?: string } | null = null;

    for (const item of formData) {
        if (item.name === 'file') {
            file = {
                data: item.data,
                filename: item.filename,
                type: item.type
            };
        }
    }

    if (!file) {
        throw createError({ statusCode: 400, message: '请上传文件' });
    }

    // 3. 调用后端解析简历
    const config = useRuntimeConfig();
    const apiBase = config.public.apiBase;

    try {
        const backendFormData = new FormData();
        const blob = new Blob([file.data], { type: file.type || 'application/octet-stream' });
        backendFormData.append('file', blob, file.filename || 'resume');

        const parseResponse = await fetch(`${apiBase}/api/parse-resume`, {
            method: 'POST',
            body: backendFormData
        });

        if (!parseResponse.ok) {
            throw new Error('简历解析失败');
        }

        const parsed = await parseResponse.json();

        // 4. 入库
        const candidate = await prisma.candidate.create({
            data: {
                userId: payload.id,
                name: parsed.name || null,
                email: parsed.email || null,
                phone: parsed.phone || null,
                location: parsed.location || null,
                currentTitle: parsed.current_title || null,
                currentCompany: parsed.current_company || null,
                yearsExperience: parsed.years_experience || null,
                skills: parsed.skills || [],
                resumeText: parsed.resume_text || '',
                resumeFilename: file.filename
            }
        });

        // 5. 可选：调用后端建立向量索引
        try {
            await fetch(`${apiBase}/api/index-candidate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_id: candidate.id,
                    user_id: payload.id,
                    resume_text: parsed.resume_text
                })
            });
        } catch (_indexError) {
            // 索引失败不影响主流程
            console.warn('Candidate indexing failed');
        }

        return {
            success: true,
            candidate: {
                id: candidate.id,
                name: candidate.name,
                currentTitle: candidate.currentTitle,
                skills: candidate.skills
            }
        };

    } catch (error: any) {
        console.error('Upload failed:', error);
        throw createError({
            statusCode: 500,
            message: error.message || '上传失败'
        });
    }
});
