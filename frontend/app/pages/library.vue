<script setup lang="ts">
/**
 * 我的人才库页面
 */
definePageMeta({ layout: 'default' });

const { user, redirectToLogin } = useAuth();

// 状态
const candidates = ref<any[]>([]);
const totalCallback = ref(0);
const currentPage = ref(1);
const searchQuery = ref('');
const isLoading = ref(false);

// 加载数据
const fetchCandidates = async () => {
    if (!user.value) return;
    
    isLoading.value = true;
    try {
        const data = await $fetch<any>('/api/candidates', {
            params: {
                page: currentPage.value,
                limit: 10,
                search: searchQuery.value
            }
        });
        candidates.value = data.list;
        totalCallback.value = data.pagination.total;
    } catch (error) {
        console.error('Failed to fetch candidates', error);
    } finally {
        isLoading.value = false;
    }
};

// 监听变化
watch([user, currentPage], () => {
    if (user.value) fetchCandidates();
});

// 搜索防抖
let searchTimeout: any;
const handleSearch = () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        currentPage.value = 1;
        fetchCandidates();
    }, 500);
};

// 删除处理
const deleteCandidate = async (id: number) => {
    if (!confirm('确定要删除这位候选人吗？')) return;
    
    try {
        await $fetch(`/api/candidates/${id}`, { method: 'DELETE' });
        fetchCandidates(); // 刷新
    } catch (error) {
        alert('删除失败');
    }
};

onMounted(() => {
    if (user.value) fetchCandidates();
});

const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('zh-CN');
};
</script>

<template>
    <div class="container">
        <div class="page-header">
            <div class="header-content">
                <h1>📊 我的人才库</h1>
                <p>管理您的私有候选人数据</p>
            </div>
            <NuxtLink to="/upload" class="btn btn-primary">
                ➕ 添加候选人
            </NuxtLink>
        </div>

        <!-- 未登录提示 -->
        <div v-if="!user" class="login-notice">
            <p>🔐 请先登录后管理人才库</p>
            <button class="btn btn-primary" @click="redirectToLogin">立即登录</button>
        </div>

        <template v-else>
            <!-- 搜索栏 -->
            <div class="toolbar">
                <div class="search-box">
                    <span class="search-icon">🔍</span>
                    <input 
                        v-model="searchQuery"
                        @input="handleSearch"
                        type="text" 
                        placeholder="搜索姓名、职位、公司或技能..."
                        class="search-input"
                    />
                </div>
            </div>

            <!-- 列表 -->
            <div v-if="loading" class="loading-state">
                加载中...
            </div>

            <div v-else-if="candidates.length === 0" class="empty-state">
                <div class="empty-icon">📂</div>
                <h3>人才库为空</h3>
                <p>上传简历开始构建您的专属人才库</p>
                <NuxtLink to="/upload" class="btn btn-outline">去上传</NuxtLink>
            </div>

            <div v-else class="candidate-grid">
                <div class="candidate-card" v-for="c in candidates" :key="c.id">
                    <div class="card-header">
                        <div class="avatar-placeholder">{{ c.name?.[0] || '?' }}</div>
                        <div class="card-title">
                            <h4>{{ c.name || '未命名候选人' }}</h4>
                            <span class="job-title">{{ c.currentTitle || '暂无职位' }}</span>
                        </div>
                        <button class="btn-icon delete-btn" @click="deleteCandidate(c.id)" title="删除">
                            🗑️
                        </button>
                    </div>

                    <div class="card-body">
                        <div class="info-row">
                            <span>🏢</span>
                            <span>{{ c.currentCompany || '暂无公司' }}</span>
                        </div>
                        <div class="info-row">
                            <span>📅</span>
                            <span>{{ c.yearsExperience ? `${c.yearsExperience}年经验` : '经验未知' }}</span>
                        </div>
                        
                        <div class="skills-row" v-if="c.skills?.length">
                            <span class="skill-tag" v-for="skill in c.skills.slice(0, 3)" :key="skill">
                                {{ skill }}
                            </span>
                            <span v-if="c.skills.length > 3" class="more-tag">+{{ c.skills.length - 3 }}</span>
                        </div>
                    </div>

                    <div class="card-footer">
                        <span class="date">入库: {{ formatDate(c.createdAt) }}</span>
                    </div>
                </div>
            </div>

            <!-- 分页 -->
            <div class="pagination" v-if="candidates.length > 0">
                <button 
                    :disabled="currentPage === 1"
                    @click="currentPage--"
                    class="page-btn"
                >上一页</button>
                <span class="page-info">第 {{ currentPage }} 页</span>
                <button 
                    :disabled="candidates.length < 10" 
                    @click="currentPage++"
                    class="page-btn"
                >下一页</button>
            </div>
        </template>
    </div>
</template>

<style scoped>
.page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
}

.page-header h1 { font-size: 2rem; margin-bottom: 4px; }
.page-header p { color: var(--color-text-secondary); }

.toolbar { margin-bottom: 24px; }

.search-box {
    position: relative;
    max-width: 400px;
}

.search-icon {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--color-text-muted);
}

.search-input {
    width: 100%;
    padding: 10px 10px 10px 40px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-bg-card);
}

.candidate-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}

.candidate-card {
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: 20px;
    transition: transform 0.2s, box-shadow 0.2s;
}

.candidate-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}

.card-header {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
}

.avatar-placeholder {
    width: 48px;
    height: 48px;
    background: linear-gradient(135deg, #3b82f6, #60a5fa);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    font-weight: 600;
}

.card-title {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: center;
}

.card-title h4 { margin: 0; font-size: 16px; }
.job-title { font-size: 13px; color: var(--color-text-secondary); }

.delete-btn {
    opacity: 0;
    transition: opacity 0.2s;
}

.candidate-card:hover .delete-btn { opacity: 1; }

.card-body { margin-bottom: 16px; }

.info-row {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    color: var(--color-text-secondary);
    margin-bottom: 8px;
}

.skills-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-top: 12px;
}

.skill-tag {
    background: var(--color-bg);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    color: var(--color-text-secondary);
}

.more-tag {
    font-size: 12px;
    color: var(--color-text-muted);
    padding: 2px 4px;
}

.card-footer {
    padding-top: 12px;
    border-top: 1px solid var(--color-border);
    font-size: 12px;
    color: var(--color-text-muted);
    text-align: right;
}

.login-notice {
    text-align: center;
    padding: 60px;
    background: var(--color-bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
}

.empty-state {
    text-align: center;
    padding: 60px;
    color: var(--color-text-secondary);
}

.empty-icon { font-size: 48px; margin-bottom: 16px; }
.btn-outline {
    border: 1px solid var(--color-primary);
    color: var(--color-primary);
    background: transparent;
    padding: 8px 16px;
    border-radius: var(--radius-md);
    margin-top: 12px;
    cursor: pointer;
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    margin-top: 32px;
}

.page-btn {
    padding: 8px 16px;
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    cursor: pointer;
}

.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
