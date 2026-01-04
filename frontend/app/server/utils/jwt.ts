/**
 * JWT 工具 - 与 INTJTech_04 保持一致
 */
import * as jose from 'jose';

const JWT_SECRET = process.env.JWT_SECRET || 'development-secret';

interface JwtPayload {
    id: number;
    email: string;
    name: string;
    avatar?: string;
}

/**
 * 验证用户 Token（来自官网跳转或 cookie）
 */
export async function verifyUserToken(token: string): Promise<JwtPayload | null> {
    try {
        const secret = new TextEncoder().encode(JWT_SECRET);
        const { payload } = await jose.jwtVerify(token, secret);
        return payload as unknown as JwtPayload;
    } catch {
        // Token 验证失败，静默返回 null
        return null;
    }
}

/**
 * 签发本地会话 Token
 */
export async function signSessionToken(user: JwtPayload): Promise<string> {
    const secret = new TextEncoder().encode(JWT_SECRET);
    const token = await new jose.SignJWT({
        id: user.id,
        email: user.email,
        name: user.name,
        avatar: user.avatar
    })
        .setProtectedHeader({ alg: 'HS256' })
        .setIssuedAt()
        .setExpirationTime('7d')
        .sign(secret);
    return token;
}
