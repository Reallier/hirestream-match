<script setup lang="ts">
/**
 * 反馈管理页面（管理员）
 * 
 * 调用后端 FastAPI 服务
 */
definePageMeta({ layout: 'default' });

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;
const { user } = useAuth();

// 检查权限
const isAdmin = computed(() => user.value?.role === 'admin');

// 状态
const feedbacks = ref<any[]>([]);
const loading = ref(true);
const total = ref(0);
const page = ref(1);
const statusFilter = ref('');

const statusOptions = [
    { value: '', label: '全部' },
    { value: 'pending', label: '待处理' },
    { value: 'reviewed', label: '已查看' },
    { value: 'resolved', label: '已解决' }
];

const statusLabels: Record<string, string> = {
    pending: '待处理',
    reviewed: '已查看',
    resolved: '已解决'
};

const typeLabels: Record<string, string> = {
    suggestion: '功能建议',
    bug: '问题反馈',
    other: '其他'
};

// 加载反馈
const loadFeedbacks = async () => {
    loading.value = true;
    try {
        const res = await $fetch<any>(`${apiBase}/api/feedback/list`, {
            credentials: 'include',
            params: {
                page: page.value,
                status: statusFilter.value || undefined
            }
        });
        if (res.success) {
            feedbacks.value = res.data;
            total.value = res.total;
        }
    } catch (error) {
        console.error('Load feedbacks error:', error);
    } finally {
        loading.value = false;
    }
};

// 更新状态
const updateStatus = async (id: number, status: string) => {
    try {
        await $fetch(`${apiBase}/api/feedback/${id}`, {
            method: 'PATCH',
            credentials: 'include',
            body: { status }
        });
        // 刷新列表
        await loadFeedbacks();
    } catch (error) {
        console.error('Update status error:', error);
    }
};

// 格式化时间
const formatTime = (date: string) => {
    return new Date(date).toLocaleString('zh-CN');
};

// 初始加载
onMounted(() => {
    loadFeedbacks();
});

// 监听筛选变化
watch(statusFilter, () => {
    page.value = 1;
    loadFeedbacks();
});
</script>

<template>
    <div class="container">
        <section class="hero">
            <h1><FaIcon icon="comment" style="margin-right: 12px;" />用户反馈管理</h1>
            <p class="hero-desc">查看和处理用户提交的反馈</p>
        </section>

        <!-- 权限检查 -->
        <div v-if="!isAdmin" class="no-permission">
            <FaIcon icon="lock" style="font-size: 48px; margin-bottom: 16px;" />
            <p>此页面仅管理员可访问</p>
        </div>

        <!-- 管理面板 -->
        <div v-else class="feedback-admin">
            <!-- 筛选 -->
            <div class="filter-bar">
                <div class="filter-item">
                    <label>状态筛选：</label>
                    <select v-model="statusFilter">
                        <option v-for="opt in statusOptions" :key="opt.value" :value="opt.value">
                            {{ opt.label }}
                        </option>
                    </select>
                </div>
                <div class="filter-stats">
                    共 {{ total }} 条反馈
                </div>
            </div>

            <!-- 加载中 -->
            <div v-if="loading" class="loading-state">
                <span class="loading-spinner"></span>
                加载中...
            </div>

            <!-- 空状态 -->
            <div v-else-if="feedbacks.length === 0" class="empty-state">
                <FaIcon icon="inbox" style="font-size: 48px; margin-bottom: 16px;" />
                <p>暂无反馈</p>
            </div>

            <!-- 反馈列表 -->
            <div v-else class="feedback-list">
                <div 
                    v-for="fb in feedbacks" 
                    :key="fb.id" 
                    class="feedback-item"
                    :class="{ resolved: fb.status === 'resolved' }"
                >
                    <div class="feedback-header">
                        <div class="feedback-meta">
                            <span class="feedback-type" :class="fb.type">{{ typeLabels[fb.type] }}</span>
                            <span class="feedback-status" :class="fb.status">{{ statusLabels[fb.status] }}</span>
                            <span class="feedback-time">{{ formatTime(fb.createdAt) }}</span>
                            <span v-if="fb.page" class="feedback-page">来自: {{ fb.page }}</span>
                        </div>
                        <div class="feedback-actions">
                            <button 
                                v-if="fb.status === 'pending'" 
                                class="btn-sm"
                                @click="updateStatus(fb.id, 'reviewed')"
                            >
                                标记已查看
                            </button>
                            <button 
                                v-if="fb.status !== 'resolved'" 
                                class="btn-sm btn-success"
                                @click="updateStatus(fb.id, 'resolved')"
                            >
                                标记已解决
                            </button>
                        </div>
                    </div>
                    <div class="feedback-content">
                        {{ fb.content }}
                    </div>
                    <div v-if="fb.contact" class="feedback-contact">
                        <FaIcon icon="user" />
                        联系方式: {{ fb.contact }}
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>

<style scoped>
.hero {
    text-align: center;
    margin-bottom: 40px;
}

.hero h1 { font-size: 2rem; margin-bottom: 12px; }
.hero-desc { color: var(--color-text-secondary); }

.no-permission {
    text-align: center;
    padding: 60px;
    color: var(--color-text-secondary);
}

.feedback-admin {
    max-width: 900px;
    margin: 0 auto;
}

.filter-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
    padding: 16px;
    background: var(--color-bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
}

.filter-item {
    display: flex;
    align-items: center;
    gap: 8px;
}

.filter-item select {
    padding: 8px 12px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: 14px;
}

.filter-stats {
    color: var(--color-text-secondary);
    font-size: 14px;
}

.loading-state, .empty-state {
    text-align: center;
    padding: 60px;
    color: var(--color-text-secondary);
}

.feedback-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.feedback-item {
    background: var(--color-bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
    padding: 20px;
}

.feedback-item.resolved {
    opacity: 0.7;
}

.feedback-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
}

.feedback-meta {
    display: flex;
    align-items: center;
    gap: 12px;
    font-size: 13px;
}

.feedback-type {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}

.feedback-type.suggestion { background: #e0f2fe; color: #0369a1; }
.feedback-type.bug { background: #fee2e2; color: #dc2626; }
.feedback-type.other { background: #f3f4f6; color: #6b7280; }

.feedback-status {
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}

.feedback-status.pending { background: #fef3c7; color: #d97706; }
.feedback-status.reviewed { background: #dbeafe; color: #2563eb; }
.feedback-status.resolved { background: #d1fae5; color: #059669; }

.feedback-time, .feedback-page {
    color: var(--color-text-muted);
}

.feedback-actions {
    display: flex;
    gap: 8px;
}

.btn-sm {
    padding: 6px 12px;
    font-size: 12px;
    border: 1px solid var(--color-border);
    background: white;
    border-radius: var(--radius-md);
    cursor: pointer;
}

.btn-sm:hover {
    background: var(--color-bg);
}

.btn-sm.btn-success {
    background: var(--color-success);
    color: white;
    border-color: var(--color-success);
}

.feedback-content {
    font-size: 15px;
    line-height: 1.6;
    white-space: pre-wrap;
}

.feedback-contact {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid var(--color-border);
    font-size: 13px;
    color: var(--color-text-secondary);
}
</style>

