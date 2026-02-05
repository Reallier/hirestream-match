<script setup lang="ts">
/**
 * 登录回调页面 - 处理从官网跳转回来的 token
 */
const route = useRoute();
const { handleLoginCallback } = useAuth();

onMounted(async () => {
    const token = route.query.token as string;
    
    if (!token) {
        navigateTo('/');
        return;
    }
    
    const success = await handleLoginCallback(token);
    
    // 跳转到首页
    navigateTo('/');
});
</script>

<template>
    <div class="callback-page">
        <div class="callback-content">
            <div class="loading-spinner"></div>
            <p>正在登录...</p>
        </div>
    </div>
</template>

<style scoped>
.callback-page {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
}

.callback-content {
    text-align: center;
}

.callback-content p {
    margin-top: 16px;
    color: var(--color-text-secondary);
}
</style>
