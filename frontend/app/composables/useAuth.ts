/**
 * 用户认证 Composable
 * 
 * 所有认证 API 调用后端 FastAPI 服务
 */
interface User {
    id: number;
    name: string;
    email: string;
    avatar?: string;
    balance: number;
    freeQuota: number;
    totalAvailable: number;
    role?: string;
}

export const useAuth = () => {
    const config = useRuntimeConfig();
    const apiBase = config.public.apiBase;

    const user = useState<User | null>('user', () => null);
    const loading = useState<boolean>('authLoading', () => true);
    const showLoginModal = useState<boolean>('showLoginModal', () => false);

    /**
     * 初始化认证（页面加载时调用）
     */
    const initAuth = async () => {
        loading.value = true;
        try {
            // 调用后端 API
            const response = await $fetch<{ success: boolean; user: User }>(`${apiBase}/api/auth/me`, {
                credentials: 'include'  // 携带 Cookie
            });
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
     * 用户登录
     */
    const login = async (username: string, password: string): Promise<{ success: boolean; message?: string }> => {
        try {
            const response = await $fetch<{ success: boolean; user: User; detail?: string }>(`${apiBase}/api/auth/login`, {
                method: 'POST',
                body: { username, password },
                credentials: 'include'
            });
            if (response.success && response.user) {
                user.value = response.user;
                return { success: true };
            }
            return { success: false, message: response.detail || '登录失败' };
        } catch (error: any) {
            return { success: false, message: error?.data?.detail || '登录失败' };
        }
    };

    /**
     * 处理登录回调（从官网跳转回来时）- 保留兼容
     */
    const handleLoginCallback = async (token: string) => {
        try {
            // 使用 token 直接初始化
            await initAuth();
            return !!user.value;
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
            const response = await $fetch<{ success: boolean; user: User }>(`${apiBase}/api/auth/me`, {
                credentials: 'include'
            });
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
        await $fetch(`${apiBase}/api/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        user.value = null;
        navigateTo('/');
    };

    /**
     * 打开登录 Modal
     */
    const openLoginModal = () => {
        showLoginModal.value = true;
    };

    /**
     * 关闭登录 Modal
     */
    const closeLoginModal = () => {
        showLoginModal.value = false;
    };

    /**
     * 登录成功处理
     */
    const handleLoginSuccess = async () => {
        await initAuth();
        closeLoginModal();
    };

    // 保留旧的 redirectToLogin 兼容，现改为打开 Modal
    const redirectToLogin = () => {
        openLoginModal();
    };

    return {
        user,
        loading,
        showLoginModal,
        initAuth,
        login,
        handleLoginCallback,
        refreshUser,
        logout,
        openLoginModal,
        closeLoginModal,
        handleLoginSuccess,
        redirectToLogin
    };
};
