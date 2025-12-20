/**
 * 退出登录
 */
export default defineEventHandler(async (event) => {
    setCookie(event, 'auth_token', '', {
        httpOnly: true,
        maxAge: 0
    });
    return { success: true };
});
