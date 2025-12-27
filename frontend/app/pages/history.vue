<script setup lang="ts">
/**
 * 匹配历史页面
 */
definePageMeta({ layout: 'default' });

const { user, redirectToLogin } = useAuth();
const records = ref<any[]>([]);
const isLoading = ref(true);

onMounted(async () => {
    if (!user.value) return;
    try {
        const { records: data } = await $fetch<any>('/api/match/history');
        records.value = data;
    } finally {
        isLoading.value = false;
    }
});

const formatDate = (date: string) => new Date(date).toLocaleString();
</script>

<template>
    <div class="container">
        <h1><FaIcon icon="history" style="margin-right: 12px;" />匹配历史</h1>
        
        <div v-if="!user" class="login-notice">
            <p>请登录查看历史记录</p>
            <button class="btn btn-primary" @click="redirectToLogin">登录</button>
        </div>

        <div v-else class="history-list">
            <div v-if="isLoading">加载中...</div>
            <div v-else-if="records.length === 0">暂无历史记录</div>
            
            <div v-else class="record-card" v-for="r in records" :key="r.id">
                <div class="record-header">
                    <span class="score-badge">{{ r.matchScore }}分</span>
                    <span class="date">{{ formatDate(r.createdAt) }}</span>
                </div>
                <div class="record-body">
                    <div class="text-preview">
                        <strong>JD:</strong> {{ r.jdText.slice(0, 100) }}...
                    </div>
                    <div class="text-preview" v-if="r.resumeFilename">
                        <strong>简历:</strong> {{ r.resumeFilename }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.record-card {
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: 16px;
    margin-bottom: 16px;
}
.record-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
}
.score-badge {
    background: var(--color-primary);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-weight: bold;
}
.text-preview {
    font-size: 13px;
    color: var(--color-text-secondary);
    margin-bottom: 4px;
}
</style>
