<script setup lang="ts">
/**
 * JD 匹配页面 - 从人才库中匹配候选人
 */
definePageMeta({ layout: 'default' });

const { user, refreshUser, redirectToLogin } = useAuth();

// 状态
const jdText = ref('');
const topK = ref(10);
const isMatching = ref(false);
const matchResults = ref<any[]>([]);
const errorMessage = ref('');
const candidateCount = ref(0);

// 获取候选人数量
const fetchCandidateCount = async () => {
    if (!user.value) return;
    try {
        const data = await $fetch<any>('/api/candidates/count');
        candidateCount.value = data.count;
    } catch (_error) {
        candidateCount.value = 0;
    }
};

onMounted(() => {
    if (user.value) {
        fetchCandidateCount();
    }
});

watch(user, (newUser) => {
    if (newUser) {
        fetchCandidateCount();
    }
});

// 执行匹配
const runMatch = async () => {
    if (!user.value) {
        redirectToLogin();
        return;
    }

    if (!jdText.value.trim()) {
        errorMessage.value = '请输入职位描述';
        return;
    }

    if (candidateCount.value === 0) {
        errorMessage.value = '您的人才库为空，请先上传简历';
        return;
    }

    if (user.value.totalAvailable <= 0) {
        errorMessage.value = '余额不足，请充值后使用';
        return;
    }

    isMatching.value = true;
    errorMessage.value = '';
    matchResults.value = [];

    try {
        const response = await $fetch<any>('/api/match/library', {
            method: 'POST',
            body: {
                jd: jdText.value,
                top_k: topK.value
            }
        });

        matchResults.value = response.results || [];
        await refreshUser();
    } catch (error: any) {
        errorMessage.value = error.data?.message || '匹配失败，请重试';
    } finally {
        isMatching.value = false;
    }
};

const formatMoney = (amount: number) => amount.toFixed(2);
</script>

<template>
    <div class="container">
        <section class="hero">
            <h1>🎯 JD 匹配</h1>
            <p class="hero-desc">输入职位描述，从您的人才库中智能匹配候选人</p>
        </section>

        <!-- 未登录提示 -->
        <div v-if="!user" class="login-notice">
            <p>🔐 请先登录后使用 JD 匹配功能</p>
            <button class="btn btn-primary" @click="redirectToLogin">立即登录</button>
        </div>

        <template v-else>
            <!-- 人才库状态 -->
            <div class="library-status">
                <div class="status-card">
                    <span class="status-icon">📊</span>
                    <div class="status-info">
                        <span class="status-label">您的人才库</span>
                        <span class="status-value">{{ candidateCount }} 份简历</span>
                    </div>
                </div>
                <NuxtLink to="/upload" class="btn btn-secondary">
                    📄 上传更多简历
                </NuxtLink>
            </div>

            <!-- JD 输入 -->
            <div class="match-form">
                <div class="form-section">
                    <h3>📋 职位描述 (JD)</h3>
                    <textarea 
                        v-model="jdText"
                        class="textarea"
                        placeholder="请输入完整的职位描述，包括岗位职责、任职要求、技能要求等..."
                        style="min-height: 250px;"
                    ></textarea>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label>返回候选人数量</label>
                        <select v-model="topK" class="select">
                            <option :value="5">Top 5</option>
                            <option :value="10">Top 10</option>
                            <option :value="20">Top 20</option>
                            <option :value="50">Top 50</option>
                        </select>
                    </div>
                </div>

                <!-- 错误提示 -->
                <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

                <!-- 提交按钮 -->
                <div class="match-submit">
                    <button 
                        class="btn btn-primary btn-lg" 
                        @click="runMatch"
                        :disabled="isMatching || candidateCount === 0"
                    >
                        <span v-if="isMatching" class="loading-spinner"></span>
                        <span v-else>🔍</span>
                        {{ isMatching ? '匹配中...' : '开始匹配' }}
                    </button>
                    <p class="match-hint">
                        当前可用额度: <strong>¥{{ formatMoney(user.totalAvailable) }}</strong>
                    </p>
                </div>
            </div>

            <!-- 匹配结果 -->
            <div v-if="matchResults.length > 0" class="match-results">
                <h3>🎯 匹配结果 ({{ matchResults.length }} 位候选人)</h3>
                
                <div class="candidate-list">
                    <div 
                        class="candidate-card"
                        v-for="(candidate, i) in matchResults" 
                        :key="candidate.id"
                    >
                        <div class="candidate-rank">{{ i + 1 }}</div>
                        <div class="candidate-info">
                            <div class="candidate-header">
                                <h4>{{ candidate.name || '未知姓名' }}</h4>
                                <div class="candidate-score">
                                    <span class="score-value">{{ candidate.match_score }}</span>
                                    <span class="score-label">匹配度</span>
                                </div>
                            </div>
                            <div class="candidate-meta">
                                <span v-if="candidate.current_title">{{ candidate.current_title }}</span>
                                <span v-if="candidate.current_company">@ {{ candidate.current_company }}</span>
                                <span v-if="candidate.years_experience">· {{ candidate.years_experience }}年经验</span>
                            </div>
                            <div class="candidate-skills" v-if="candidate.skills?.length">
                                <span class="skill-tag" v-for="skill in candidate.skills.slice(0, 5)" :key="skill">
                                    {{ skill }}
                                </span>
                            </div>
                            <div class="candidate-highlights" v-if="candidate.highlights">
                                <p>{{ candidate.highlights }}</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </template>
    </div>
</template>

<style scoped>
.hero {
    text-align: center;
    margin-bottom: 40px;
}

.hero h1 { font-size: 2.5rem; margin-bottom: 12px; }
.hero-desc { color: var(--color-text-secondary); font-size: 18px; }

.login-notice {
    text-align: center;
    padding: 60px;
    background: var(--color-bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
}

.login-notice p {
    margin-bottom: 20px;
    font-size: 16px;
    color: var(--color-text-secondary);
}

.library-status {
    display: flex;
    align-items: center;
    justify-content: space-between;
    background: var(--color-bg-card);
    padding: 20px 24px;
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
    margin-bottom: 24px;
}

.status-card {
    display: flex;
    align-items: center;
    gap: 16px;
}

.status-icon { font-size: 32px; }
.status-info { display: flex; flex-direction: column; }
.status-label { font-size: 13px; color: var(--color-text-muted); }
.status-value { font-size: 20px; font-weight: 600; color: var(--color-primary); }

.match-form {
    max-width: 800px;
    margin: 0 auto;
}

.form-section {
    background: var(--color-bg-card);
    padding: 24px;
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
    margin-bottom: 16px;
}

.form-section h3 { font-size: 16px; margin-bottom: 16px; }

.form-row {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
}

.form-group {
    flex: 1;
}

.form-group label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 8px;
}

.select {
    width: 100%;
    padding: 12px 16px;
    font-size: 14px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    background: var(--color-bg-card);
}

.match-submit {
    text-align: center;
    margin-top: 24px;
}

.match-hint {
    margin-top: 12px;
    font-size: 13px;
    color: var(--color-text-secondary);
}

.match-hint strong { color: var(--color-primary); }

.error-message {
    background: rgba(239, 68, 68, 0.1);
    color: var(--color-danger);
    padding: 12px 16px;
    border-radius: var(--radius-md);
    margin-top: 16px;
    text-align: center;
}

.match-results {
    margin-top: 40px;
}

.match-results h3 {
    font-size: 18px;
    margin-bottom: 20px;
}

.candidate-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.candidate-card {
    display: flex;
    gap: 20px;
    background: var(--color-bg-card);
    padding: 24px;
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
}

.candidate-rank {
    width: 40px;
    height: 40px;
    background: var(--color-primary);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 16px;
    flex-shrink: 0;
}

.candidate-info { flex: 1; }

.candidate-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 8px;
}

.candidate-header h4 {
    font-size: 18px;
    margin: 0;
}

.candidate-score {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
}

.score-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--color-primary);
}

.score-label {
    font-size: 11px;
    color: var(--color-text-muted);
}

.candidate-meta {
    font-size: 14px;
    color: var(--color-text-secondary);
    margin-bottom: 12px;
}

.candidate-skills {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 12px;
}

.skill-tag {
    padding: 4px 10px;
    background: var(--color-bg);
    border-radius: 4px;
    font-size: 12px;
    color: var(--color-text-secondary);
}

.candidate-highlights {
    font-size: 13px;
    color: var(--color-text-secondary);
    padding: 12px;
    background: var(--color-bg);
    border-radius: var(--radius-md);
}
</style>
