<script setup lang="ts">
/**
 * 我的人才库页面 - 列表式布局
 */
definePageMeta({ layout: 'default' });

const config = useRuntimeConfig();
const apiBase = config.public.apiBase;
const { user, redirectToLogin } = useAuth();
const { getCandidates, deleteCandidate: doDeleteCandidate, searchCandidates } = useCandidates();

// 状态
const candidates = ref<any[]>([]);
const totalCount = ref(0);
const currentPage = ref(1);
const searchQuery = ref('');
const isLoading = ref(false);
const isSearchMode = ref(false);

// 加载候选人列表
const fetchCandidates = async () => {
    if (!user.value) return;
    
    isLoading.value = true;
    isSearchMode.value = false;
    try {
        const skip = (currentPage.value - 1) * 20;
        const data = await getCandidates({ skip, limit: 20 });
        candidates.value = data.candidates;
        totalCount.value = data.total;
    } catch (error) {
        console.error('Failed to fetch candidates', error);
    } finally {
        isLoading.value = false;
    }
};

// 语义搜索
const performSearch = async () => {
    if (!user.value) return redirectToLogin();
    if (!searchQuery.value.trim()) {
        // 无搜索词，显示全部
        fetchCandidates();
        return;
    }

    isLoading.value = true;
    isSearchMode.value = true;
    try {
        candidates.value = await searchCandidates(searchQuery.value, 50);
        totalCount.value = candidates.value.length;
    } catch {
        candidates.value = [];
    } finally {
        isLoading.value = false;
    }
};

// 删除处理
const deleteCandidate = async (id: number) => {
    if (!confirm('确定要删除这位候选人吗？')) return;
    
    const success = await doDeleteCandidate(id);
    if (success) {
        if (isSearchMode.value) {
            candidates.value = candidates.value.filter(c => c.id !== id);
        } else {
            fetchCandidates();
        }
    } else {
        alert('删除失败');
    }
};

// 清空搜索
const clearSearch = () => {
    searchQuery.value = '';
    fetchCandidates();
};

// 监听页码变化
watch([user, currentPage], () => {
    if (user.value && !isSearchMode.value) fetchCandidates();
});

onMounted(() => {
    if (user.value) fetchCandidates();
});

const formatDate = (date: string) => {
    return new Date(date).toLocaleDateString('zh-CN');
};

// 格式化技能列表
const formatSkills = (skills: string[]) => {
    if (!skills || skills.length === 0) return '-';
    const shown = skills.slice(0, 4).join(', ');
    return skills.length > 4 ? `${shown} +${skills.length - 4}` : shown;
};
</script>

<template>
    <div class="container">
        <div class="page-header">
            <div class="header-content">
                <h1><FaIcon icon="users" style="margin-right: 12px;" />我的人才库</h1>
                <p>共 {{ totalCount }} 位候选人</p>
            </div>
            <NuxtLink to="/upload" class="btn btn-primary">
                <FaIcon icon="plus" style="margin-right: 6px;" />添加候选人
            </NuxtLink>
        </div>

        <!-- 未登录提示 -->
        <div v-if="!user" class="login-notice">
            <p><FaIcon icon="sign-in-alt" style="margin-right: 6px;" />请先登录后管理人才库</p>
            <button class="btn btn-primary" @click="redirectToLogin">立即登录</button>
        </div>

        <template v-else>
            <!-- 搜索栏 -->
            <div class="toolbar">
                <div class="search-box">
                    <span class="search-icon"><FaIcon icon="search" /></span>
                    <input 
                        v-model="searchQuery"
                        @keyup.enter="performSearch"
                        type="text" 
                        placeholder="搜索姓名、职位、公司或技能..."
                        class="search-input"
                    />
                    <button v-if="searchQuery" class="clear-btn" @click="clearSearch">
                        <FaIcon icon="times" />
                    </button>
                </div>
                <button class="btn btn-primary" @click="performSearch" :disabled="isLoading">
                    {{ isLoading ? '搜索中...' : '搜索' }}
                </button>
            </div>

            <!-- 搜索模式提示 -->
            <div v-if="isSearchMode" class="search-hint">
                <span>搜索结果：「{{ searchQuery }}」找到 {{ candidates.length }} 位匹配候选人</span>
                <button class="btn-link" @click="clearSearch">清除搜索</button>
            </div>

            <!-- 加载中 -->
            <div v-if="isLoading" class="loading-state">
                <FaIcon icon="spinner" spin /> 加载中...
            </div>

            <!-- 空状态 -->
            <div v-else-if="candidates.length === 0" class="empty-state">
                <div class="empty-icon"><FaIcon icon="folder-open" /></div>
                <h3>{{ isSearchMode ? '未找到匹配的候选人' : '人才库为空' }}</h3>
                <p>{{ isSearchMode ? '换个关键词试试？' : '上传简历开始构建您的专属人才库' }}</p>
                <NuxtLink v-if="!isSearchMode" to="/upload" class="btn btn-outline">去上传</NuxtLink>
            </div>

            <!-- 候选人列表 -->
            <div v-else class="candidate-table">
                <table>
                    <thead>
                        <tr>
                            <th class="col-name">姓名</th>
                            <th class="col-title">职位</th>
                            <th class="col-company">公司</th>
                            <th class="col-exp">经验</th>
                            <th class="col-skills">技能</th>
                            <th class="col-date">入库时间</th>
                            <th class="col-resume">简历</th>
                            <th class="col-action">操作</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr v-for="c in candidates" :key="c.id">
                            <td class="col-name">
                                <span class="name-text">{{ c.name || '未命名' }}</span>
                            </td>
                            <td class="col-title">{{ c.currentTitle || '-' }}</td>
                            <td class="col-company">{{ c.currentCompany || '-' }}</td>
                            <td class="col-exp">{{ c.yearsExperience ? `${c.yearsExperience}年` : '-' }}</td>
                            <td class="col-skills">
                                <span class="skills-text">{{ formatSkills(c.skills) }}</span>
                            </td>
                            <td class="col-date">{{ formatDate(c.createdAt) }}</td>
                            <td class="col-resume">
                                <a v-if="c.resumeUrl" :href="`${apiBase}${c.resumeUrl}`" target="_blank" class="resume-link">
                                    <FaIcon icon="file-pdf" /> PDF
                                </a>
                                <span v-else class="no-resume">-</span>
                            </td>
                            <td class="col-action">
                                <button class="btn-icon delete-btn" @click="deleteCandidate(c.id)" title="删除">
                                    <FaIcon icon="trash" />
                                </button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- 分页 -->
            <div class="pagination" v-if="!isSearchMode && candidates.length > 0">
                <button 
                    :disabled="currentPage === 1"
                    @click="currentPage--"
                    class="page-btn"
                >上一页</button>
                <span class="page-info">第 {{ currentPage }} 页 / 共 {{ Math.ceil(totalCount / 20) }} 页</span>
                <button 
                    :disabled="candidates.length < 20" 
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
    margin-bottom: 24px;
}

.page-header h1 { font-size: 1.75rem; margin-bottom: 4px; }
.page-header p { color: var(--color-text-secondary); font-size: 14px; }

.toolbar { 
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
}

.search-box {
    position: relative;
    flex: 1;
    max-width: 500px;
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
    padding: 10px 36px 10px 40px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-bg-card);
    font-size: 14px;
}

.clear-btn {
    position: absolute;
    right: 8px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    padding: 4px 8px;
}

.search-hint {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    margin-bottom: 20px;
    font-size: 14px;
    color: var(--color-text-secondary);
}

.btn-link {
    background: none;
    border: none;
    color: var(--color-primary);
    cursor: pointer;
    text-decoration: underline;
}

/* 表格样式 */
.candidate-table {
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    overflow: hidden;
}

table {
    width: 100%;
    border-collapse: collapse;
}

thead {
    background: var(--color-bg);
}

th, td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid var(--color-border);
    font-size: 14px;
}

th {
    font-weight: 600;
    color: var(--color-text-secondary);
    font-size: 13px;
}

tbody tr:hover {
    background: var(--color-bg);
}

tbody tr:last-child td {
    border-bottom: none;
}

.col-name { width: 120px; }
.col-title { width: 150px; }
.col-company { width: 150px; }
.col-exp { width: 80px; text-align: center; }
.col-skills { min-width: 200px; }
.col-date { width: 100px; }
.col-resume { width: 70px; text-align: center; }
.col-action { width: 60px; text-align: center; }

.resume-link {
    color: var(--color-primary);
    text-decoration: none;
    font-size: 13px;
    display: inline-flex;
    align-items: center;
    gap: 4px;
}

.resume-link:hover {
    text-decoration: underline;
}

.no-resume {
    color: var(--color-text-muted);
}

.name-text {
    font-weight: 500;
    color: var(--color-text);
}

.skills-text {
    color: var(--color-text-secondary);
    font-size: 13px;
}

.delete-btn {
    opacity: 0.5;
    transition: opacity 0.2s;
}

tbody tr:hover .delete-btn { opacity: 1; }

.btn-icon {
    background: none;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    padding: 6px;
}

.btn-icon:hover {
    color: #ef4444;
}

/* 空状态 */
.login-notice, .empty-state {
    text-align: center;
    padding: 60px;
    background: var(--color-bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
}

.empty-icon { font-size: 48px; margin-bottom: 16px; color: var(--color-text-muted); }

.loading-state {
    text-align: center;
    padding: 40px;
    color: var(--color-text-secondary);
}

.btn-outline {
    border: 1px solid var(--color-primary);
    color: var(--color-primary);
    background: transparent;
    padding: 8px 16px;
    border-radius: var(--radius-md);
    margin-top: 12px;
    cursor: pointer;
}

/* 分页 */
.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    margin-top: 24px;
}

.page-btn {
    padding: 8px 16px;
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    cursor: pointer;
    font-size: 14px;
}

.page-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.page-info {
    font-size: 14px;
    color: var(--color-text-secondary);
}
</style>
