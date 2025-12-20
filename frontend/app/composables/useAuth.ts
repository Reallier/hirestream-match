/**
 * 用户认证 Composable
 */
interface User {
    id: number;
    name: string;
    email: string;
    avatar?: string;
    balance: number;
    freeQuota: number;
    totalAvailable: number;
}

export const useAuth = () => {
    const user = useState<User | null>('user', () => null);
    const loading = useState<boolean>('authLoading', () => true);

    /**
     * 初始化认证（页面加载时调用）
     */
    const initAuth = async () => {
        loading.value = true;
        try {
            const response = await $fetch<{ success: boolean; user: User }>('/api/auth/me');
            if (response.success && response.user) {
                user.value = response.user;
            }
        } catch (error) {
            user.value = null;
        } finally {
            loading.value = false;
        }
    };

    /**
     * 处理登录回调（从官网跳转回来时）
     */
    const handleLoginCallback = async (token: string) => {
        try {
            const response = await $fetch<{ success: boolean; user: User }>('/api/auth/callback', {
                method: 'POST',
                body: { token }
            });
            if (response.success && response.user) {
                user.value = response.user;
                return true;
            }
        } catch (error) {
            console.error('Login callback failed:', error);
        }
        return false;
    };

    /**
     * 刷新用户信息（余额等）
     */
    const refreshUser = async () => {
        if (!user.value) return;
        try {
            const response = await $fetch<{ success: boolean; user: User }>('/api/auth/me');
            if (response.success && response.user) {
                user.value = response.user;
            }
        } catch (error) {
            console.error('Refresh user failed:', error);
        }
    };

    /**
     * 退出登录
     */
    const logout = async () => {
        await $fetch('/api/auth/logout', { method: 'POST' });
        user.value = null;
        navigateTo('/');
    };

    /**
     * 跳转到官网登录
     */
    const redirectToLogin = () => {
        const returnUrl = encodeURIComponent(window.location.origin + '/auth/callback');
        window.location.href = `https://intjtech.reallier.top:5443/login?redirect=talentai&returnUrl=${returnUrl}`;
    };

    return {
        user,
        loading,
        initAuth,
        handleLoginCallback,
        refreshUser,
        logout,
        redirectToLogin
    };
};
