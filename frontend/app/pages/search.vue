<script setup lang="ts">
/**
 * 人才搜索页面
 */
definePageMeta({ layout: 'default' });

const { user, redirectToLogin } = useAuth();

const query = ref('');
const results = ref<any[]>([]);
const isSearching = ref(false);
const hasSearched = ref(false);

const performSearch = async () => {
    if (!user.value) return redirectToLogin();
    if (!query.value.trim()) return;

    isSearching.value = true;
    hasSearched.value = true;
    results.value = [];

    try {
        const { results: data } = await $fetch<any>('/api/search/candidates', {
            method: 'POST',
            body: { query: query.value }
        });
        results.value = data;
    } catch (error) {
        console.error('Search failed', error);
    } finally {
        isSearching.value = false;
    }
};

// 高亮关键词
const highlight = (text: string) => {
    if (!query.value) return text;
    const regex = new RegExp(`(${query.value})`, 'gi');
    return text?.replace(regex, '<mark>$1</mark>') || '';
};
</script>

<template>
    <div class="container">
        <section class="search-hero">
            <h1><FaIcon icon="search" style="margin-right: 12px;" />人才搜索</h1>
            <p>输入关键词，在您的人才库中快速查找候选人</p>
            
            <div class="search-bar">
                <input 
                    v-model="query" 
                    @keyup.enter="performSearch"
                    type="text" 
                    placeholder="例如：高级前端开发 Vue3..." 
                    class="search-input"
                >
                <button class="btn btn-primary search-btn" @click="performSearch" :disabled="isSearching">
                    {{ isSearching ? '搜索中...' : '搜索' }}
                </button>
            </div>
        </section>

        <!-- 结果区域 -->
        <div v-if="hasSearched" class="results-section">
            <h3 class="results-count">找到 {{ results.length }} 位匹配候选人</h3>

            <div v-if="results.length > 0" class="results-grid">
                <div class="candidate-card" v-for="c in results" :key="c.id">
                    <div class="card-header">
                        <h4>{{ c.name }}</h4>
                        <span class="score" v-if="c.yearsExperience">{{ c.yearsExperience }}年经验</span>
                    </div>
                    <div class="card-body">
                        <p><strong>职位:</strong> <span v-html="highlight(c.currentTitle || '未知')"></span></p>
                        <p><strong>公司:</strong> <span v-html="highlight(c.currentCompany || '未知')"></span></p>
                        <div class="skills" v-if="c.skills?.length">
                            <span class="skill-tag" v-for="s in c.skills.slice(0,5)" :key="s" v-html="highlight(s)"></span>
                        </div>
                    </div>
                    <div class="card-footer">
                        <NuxtLink :to="`/library`" class="btn-link">查看详情 →</NuxtLink>
                    </div>
                </div>
            </div>

            <div v-else class="empty-state">
                <p>未找到匹配的候选人，换个关键词试试？</p>
            </div>
        </div>
    </div>
</template>

<style scoped>
.search-hero {
    text-align: center;
    margin-bottom: 40px;
}
.search-bar {
    max-width: 600px;
    margin: 24px auto;
    display: flex;
    gap: 12px;
}
.search-input {
    flex: 1;
    padding: 12px 16px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    font-size: 16px;
}
.search-btn {
    padding: 0 32px;
}
.results-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 20px;
}
.candidate-card {
    background: var(--color-bg-card);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
    padding: 20px;
}
.skill-tag {
    background: var(--color-bg);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    margin-right: 4px;
}
:deep(mark) {
    background-color: rgba(255, 215, 0, 0.4);
    color: inherit;
    padding: 0 2px;
    border-radius: 2px;
}
</style>
