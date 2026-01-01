/**
 * 退出登录
 */
export default defineEventHandler(async (event) => {
    const isDev = process.env.NODE_ENV !== 'production';
    setCookie(event, 'auth_token', '', {
        httpOnly: true,
        maxAge: 0,
        path: '/',
        ...(isDev ? {} : { domain: '.reallier.top', secure: true }),
        sameSite: 'lax'
    });
    return { success: true };
});
