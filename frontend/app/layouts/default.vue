<script setup lang="ts">
/**
 * 默认布局 - Header + 导航 + Footer
 */
const route = useRoute();
const { user, loading, initAuth, refreshUser, redirectToLogin } = useAuth();

// 初始化认证
onMounted(() => {
    initAuth();
});

// 导航菜单
const navItems = [
    { path: '/', label: '⚡ 即时匹配', icon: '⚡' },
    { path: '/upload', label: '📄 简历入库', icon: '📄' },
    { path: '/library', label: '📊 我的人才库', icon: '📊' },
    { path: '/search', label: '🔍 人才搜索', icon: '🔍' },
    { path: '/match', label: '🎯 JD 匹配', icon: '🎯' },
    { path: '/history', label: '📜 历史记录', icon: '📜' },
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
                        <span class="header-logo-icon">🎯</span>
                        <span>TalentAI</span>
                    </NuxtLink>
                    
                    <!-- 导航 -->
                    <nav class="nav">
                        <NuxtLink 
                            v-for="item in navItems" 
                            :key="item.path"
                            :to="item.path"
                            class="nav-item"
                            :class="{ active: route.path === item.path }"
                        >
                            {{ item.label }}
                        </NuxtLink>
                    </nav>
                </div>
                
                <div class="user-menu" v-if="!loading">
                    <template v-if="user">
                        <div class="user-balance">
                            <span>💰</span>
                            <span class="user-balance-amount">¥{{ formatMoney(user.totalAvailable) }}</span>
                        </div>
                        <img 
                            :src="user.avatar || `https://api.dicebear.com/7.x/avataaars/svg?seed=${user.id}`"
                            :alt="user.name"
                            class="user-avatar"
                            :title="user.name"
                        />
                    </template>
                    <template v-else>
                        <button class="btn btn-primary" @click="redirectToLogin">
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
            </div>
        </footer>
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
    padding: 8px 16px;
    font-size: 14px;
    color: var(--color-text-secondary);
    text-decoration: none;
    border-radius: 6px;
    transition: all 0.2s;
}

.nav-item:hover {
    background: var(--color-bg);
    color: var(--color-text);
}

.nav-item.active {
    background: var(--color-primary);
    color: white;
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

.user-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border: 2px solid var(--color-border);
    cursor: pointer;
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

@media (max-width: 768px) {
    .nav {
        display: none;
    }
}
</style>
