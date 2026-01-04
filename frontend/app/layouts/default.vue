<script setup lang="ts">
/**
 * 默认布局 - Header + 导航 + Footer
 */
const route = useRoute();
const router = useRouter();
const { user, loading, showLoginModal, initAuth, handleLoginCallback, refreshUser, redirectToLogin, handleLoginSuccess, logout } = useAuth();

// 用户菜单状态
const showUserMenu = ref(false);

const toggleUserMenu = () => {
    showUserMenu.value = !showUserMenu.value;
};

const handleLogout = async () => {
    showUserMenu.value = false;
    await logout();
};

// 点击外部关闭菜单
if (typeof window !== 'undefined') {
    window.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        if (!target.closest('.user-menu-wrapper')) {
            showUserMenu.value = false;
        }
    });
}

// 初始化认证
onMounted(async () => {
    // 检查 URL 中是否有 token 参数（从官网 hirestream-redirect 跳转过来）
    const urlToken = route.query.token as string;
    if (urlToken) {
        // 有 token，先进行登录回调处理
        await handleLoginCallback(urlToken);
        // 清除 URL 中的 token 参数，保留其他参数
        const query = { ...route.query };
        delete query.token;
        router.replace({ path: route.path, query });
    } else {
        // 没有 token，正常初始化认证（从 cookie 读取）
        await initAuth();
    }
});

// 导航菜单 - 使用 Font Awesome 图标
const navItems = [
    { path: '/', label: '即时匹配', icon: 'bolt' },
    { path: '/upload', label: '简历入库', icon: 'cloud-upload-alt' },
    { path: '/library', label: '我的人才库', icon: 'users' },
    { path: '/search', label: '人才搜索', icon: 'search' },
    { path: '/match', label: 'JD 匹配', icon: 'bullseye' },
    { path: '/history', label: '历史记录', icon: 'history' },
];

// 格式化金额
const formatMoney = (amount: number) => {
    return amount.toFixed(2);
};
</script>

<template>
    <div class="app-layout">
        <!-- Header -->
        <header class="header">
            <div class="container header-inner">
                <div class="header-left">
                    <NuxtLink to="/" class="header-logo">
                        <span class="header-logo-icon">
                            <FaIcon icon="bullseye" />
                        </span>
                        <span>TalentAI</span>
                    </NuxtLink>
                    
                    <!-- 导航 -->
                    <nav class="nav">
                        <template v-for="item in navItems" :key="item.path">
                            <!-- 已开放的功能 -->
                            <NuxtLink 
                                v-if="!item.disabled"
                                :to="item.path"
                                class="nav-item"
                                :class="{ active: route.path === item.path }"
                            >
                                <FaIcon :icon="item.icon" class="nav-icon" />
                                <span>{{ item.label }}</span>
                            </NuxtLink>
                            <!-- 暂未开放的功能 -->
                            <div 
                                v-else
                                class="nav-item nav-item-disabled"
                                :title="'暂未开放'"
                            >
                                <FaIcon :icon="item.icon" class="nav-icon" />
                                <span>{{ item.label }}</span>
                                <span class="coming-soon-badge">即将上线</span>
                            </div>
                        </template>
                    </nav>
                </div>
                
                <div class="user-menu" v-if="!loading">
                    <template v-if="user">
                        <div class="user-balance">
                            <FaIcon icon="wallet" class="balance-icon" />
                            <span class="user-balance-amount">¥{{ formatMoney(user.totalAvailable) }}</span>
                        </div>
                        <div class="user-menu-wrapper">
                            <img 
                                :src="user.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.id}`"
                                :alt="user.name"
                                class="user-avatar"
                                :title="user.name"
                                @click.stop="toggleUserMenu"
                            />
                            <div v-show="showUserMenu" class="user-dropdown">
                                <div class="user-dropdown-header">
                                    <div class="user-dropdown-avatar">{{ user.name?.[0] || 'U' }}</div>
                                    <div class="user-dropdown-info">
                                        <div class="user-dropdown-name">{{ user.name || user.email }}</div>
                                        <div class="user-dropdown-email">{{ user.email }}</div>
                                    </div>
                                </div>
                                <div class="user-dropdown-divider"></div>
                                <button class="user-dropdown-item" @click="handleLogout">
                                    <FaIcon icon="sign-out-alt" />
                                    <span>退出登录</span>
                                </button>
                            </div>
                        </div>
                    </template>
                    <template v-else>
                        <button class="btn btn-primary" @click="redirectToLogin">
                            <FaIcon icon="sign-in-alt" style="margin-right: 6px;" />
                            登录
                        </button>
                    </template>
                </div>
            </div>
        </header>

        <!-- Main Content -->
        <main class="main-content">
            <slot />
        </main>

        <!-- Footer -->
        <footer class="footer">
            <div class="container">
                <p>© 2025 TalentAI · 智能招聘匹配系统</p>
                <div class="footer-links">
                    <NuxtLink to="/terms">用户协议</NuxtLink>
                    <span class="divider">|</span>
                    <NuxtLink to="/privacy">隐私政策</NuxtLink>
                </div>
            </div>
        </footer>

        <!-- 反馈组件 -->
        <FeedbackWidget />
        
        <!-- 登录 Modal -->
        <LoginModal 
            v-model="showLoginModal" 
            @success="handleLoginSuccess"
        />
    </div>
</template>

<style scoped>
.app-layout {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

.header {
    background: var(--color-bg-card);
    border-bottom: 1px solid var(--color-border);
    position: sticky;
    top: 0;
    z-index: 100;
}

.header-inner {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 64px;
}

.header-left {
    display: flex;
    align-items: center;
    gap: 32px;
}

.header-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 20px;
    font-weight: 700;
    color: var(--color-text);
    text-decoration: none;
}

.header-logo-icon {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 16px;
}

.nav {
    display: flex;
    gap: 4px;
}

.nav-item {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 16px;
    font-size: 14px;
    color: var(--color-text-secondary);
    text-decoration: none;
    border-radius: 6px;
    transition: all 0.2s;
}

.nav-icon {
    font-size: 14px;
    opacity: 0.8;
}

.nav-item:hover {
    background: var(--color-bg);
    color: var(--color-text);
}

.nav-item.active {
    background: var(--color-primary);
    color: white;
}

.nav-item.active .nav-icon {
    opacity: 1;
}

.nav-item-disabled {
    cursor: not-allowed;
    opacity: 0.5;
    position: relative;
}

.nav-item-disabled:hover {
    background: transparent;
    color: var(--color-text-secondary);
}

.coming-soon-badge {
    position: absolute;
    top: -6px;
    right: -8px;
    background: linear-gradient(135deg, #ff6b6b, #ff8e53);
    color: white;
    font-size: 9px;
    padding: 2px 4px;
    border-radius: 4px;
    font-weight: 600;
    white-space: nowrap;
}

.balance-icon {
    font-size: 14px;
    color: var(--color-primary);
}

.user-menu {
    display: flex;
    align-items: center;
    gap: 16px;
}

.user-balance {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: var(--color-bg);
    border-radius: 8px;
    font-size: 13px;
}

.user-balance-amount {
    font-weight: 600;
    color: var(--color-primary);
}

.user-menu-wrapper {
    position: relative;
}

.user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 2px solid var(--color-border);
    cursor: pointer;
    transition: border-color 0.2s;
}

.user-avatar:hover {
    border-color: var(--color-primary);
}

.user-dropdown {
    position: absolute;
    top: 100%;
    right: 0;
    margin-top: 8px;
    width: 220px;
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    overflow: hidden;
}

.user-dropdown-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px;
}

.user-dropdown-avatar {
    width: 40px;
    height: 40px;
    background: var(--color-primary);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 16px;
    font-weight: 600;
}

.user-dropdown-info {
    flex: 1;
    min-width: 0;
}

.user-dropdown-name {
    font-size: 14px;
    font-weight: 600;
    color: var(--color-text);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.user-dropdown-email {
    font-size: 12px;
    color: var(--color-text-muted);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.user-dropdown-divider {
    height: 1px;
    background: var(--color-border);
}

.user-dropdown-item {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 12px 16px;
    background: transparent;
    border: none;
    font-size: 14px;
    color: var(--color-text-secondary);
    cursor: pointer;
    transition: all 0.2s;
}

.user-dropdown-item:hover {
    background: var(--color-bg);
    color: var(--color-text);
}

.main-content {
    flex: 1;
    padding: 32px 0;
}

.footer {
    background: var(--color-bg-card);
    border-top: 1px solid var(--color-border);
    padding: 20px 0;
    text-align: center;
    color: var(--color-text-muted);
    font-size: 13px;
}

.footer-links {
    margin-top: 8px;
}

.footer-links a {
    color: var(--color-text-muted);
    text-decoration: none;
}

.footer-links a:hover {
    color: var(--color-primary);
}

.footer-links .divider {
    margin: 0 8px;
    opacity: 0.5;
}

@media (max-width: 768px) {
    .nav {
        display: none;
    }
}
</style>
