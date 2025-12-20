<script setup lang="ts">
/**
 * TalentAI 首页 - 即时匹配
 */
definePageMeta({ layout: 'default' });

const { user, refreshUser, redirectToLogin } = useAuth();
const config = useRuntimeConfig();

// 表单数据
const jdText = ref('');
const resumeFile = ref<File | null>(null);
const resumeText = ref('');
const isDragging = ref(false);

// 匹配状态
const isMatching = ref(false);
const matchResult = ref<any>(null);
const matchError = ref('');

// 文件输入引用
const fileInput = ref<HTMLInputElement | null>(null);

// 处理文件选择
const handleFileSelect = (event: Event) => {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files[0]) {
        resumeFile.value = input.files[0];
        resumeText.value = '';
    }
};

// 处理拖拽
const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    isDragging.value = true;
};

const handleDragLeave = () => {
    isDragging.value = false;
};

const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    isDragging.value = false;
    if (e.dataTransfer?.files[0]) {
        resumeFile.value = e.dataTransfer.files[0];
        resumeText.value = '';
    }
};

// 执行匹配
const runMatch = async () => {
    if (!user.value) {
        redirectToLogin();
        return;
    }

    if (!jdText.value.trim()) {
        matchError.value = '请输入职位描述';
        return;
    }

    if (!resumeFile.value && !resumeText.value.trim()) {
        matchError.value = '请上传简历或输入简历文本';
        return;
    }

    if (user.value.totalAvailable <= 0) {
        matchError.value = '余额不足，请充值后使用';
        return;
    }

    isMatching.value = true;
    matchError.value = '';
    matchResult.value = null;

    try {
        const formData = new FormData();
        formData.append('jd', jdText.value);
        
        if (resumeFile.value) {
            formData.append('resume', resumeFile.value);
        } else {
            formData.append('resume_text', resumeText.value);
        }

        const response = await $fetch<any>('/api/match/instant', {
            method: 'POST',
            body: formData
        });

        matchResult.value = response;
        await refreshUser();
    } catch (error: any) {
        matchError.value = error.data?.message || '匹配失败，请重试';
    } finally {
        isMatching.value = false;
    }
};

const formatMoney = (amount: number) => amount.toFixed(2);
</script>

<template>
    <div class="container">
        <!-- Hero -->
        <section class="hero">
            <h1>⚡ 即时匹配</h1>
            <p class="hero-desc">上传简历，输入 JD，AI 秒级分析匹配度（不入库）</p>
        </section>

        <!-- 匹配表单 -->
        <div class="match-form">
            <div class="match-grid">
                <!-- 简历输入 -->
                <div class="match-section">
                    <h3>📄 简历</h3>
                    
                    <div 
                        class="upload-area"
                        :class="{ dragover: isDragging, 'has-file': resumeFile }"
                        @click="fileInput?.click()"
                        @dragover="handleDragOver"
                        @dragleave="handleDragLeave"
                        @drop="handleDrop"
                    >
                        <template v-if="resumeFile">
                            <p style="font-size: 32px;">✅</p>
                            <p style="font-weight: 500; margin-top: 8px;">{{ resumeFile.name }}</p>
                            <p class="upload-hint">点击更换文件</p>
                        </template>
                        <template v-else>
                            <p style="font-size: 32px;">📄</p>
                            <p style="font-weight: 500; margin-top: 8px;">点击或拖拽上传简历</p>
                            <p class="upload-hint">支持 PDF、图片格式</p>
                        </template>
                    </div>
                    <input 
                        ref="fileInput"
                        type="file" 
                        accept=".pdf,.jpg,.jpeg,.png,.gif,.webp"
                        style="display: none;"
                        @change="handleFileSelect"
                    />

                    <div class="divider"><span>或</span></div>

                    <textarea 
                        v-model="resumeText"
                        class="textarea"
                        placeholder="在此粘贴简历文本内容..."
                        :disabled="!!resumeFile"
                        style="min-height: 150px;"
                    ></textarea>
                </div>

                <!-- JD 输入 -->
                <div class="match-section">
                    <h3>📋 职位描述 (JD)</h3>
                    <textarea 
                        v-model="jdText"
                        class="textarea"
                        placeholder="请输入完整的职位描述..."
                        style="min-height: 350px;"
                    ></textarea>
                </div>
            </div>

            <!-- 错误提示 -->
            <div v-if="matchError" class="error-message">{{ matchError }}</div>

            <!-- 提交按钮 -->
            <div class="match-submit">
                <button class="btn btn-primary btn-lg" @click="runMatch" :disabled="isMatching">
                    <span v-if="isMatching" class="loading-spinner"></span>
                    <span v-else>🚀</span>
                    {{ isMatching ? '分析中...' : '开始匹配分析' }}
                </button>
                <p class="match-hint" v-if="!user">
                    <span class="login-hint">🔐 登录后即可使用 · </span>
                    <a href="javascript:void(0)" @click="redirectToLogin" class="login-link">立即登录</a>
                </p>
                <p class="match-hint" v-else>
                    当前可用额度: <strong>¥{{ formatMoney(user.totalAvailable) }}</strong>
                </p>
            </div>
        </div>

        <!-- 匹配结果 -->
        <div v-if="matchResult" class="match-result card">
            <h3 style="margin-bottom: 20px;">📊 匹配分析报告</h3>
            
            <div class="score-display">
                <div class="score-number">{{ matchResult.match_score }}</div>
                <div class="score-label">匹配度</div>
            </div>

            <div class="result-grid" style="margin-top: 24px;">
                <div class="result-card success">
                    <div class="result-card-title"><span>✅</span> 匹配优势</div>
                    <ul class="result-card-list">
                        <li v-for="(item, i) in matchResult.advantages" :key="i">{{ item }}</li>
                    </ul>
                </div>

                <div class="result-card warning">
                    <div class="result-card-title"><span>⚠️</span> 潜在风险</div>
                    <ul class="result-card-list">
                        <li v-for="(item, i) in matchResult.risks" :key="i">{{ item }}</li>
                    </ul>
                </div>

                <div class="result-card info">
                    <div class="result-card-title"><span>💡</span> 建议</div>
                    <p style="font-size: 13px; color: var(--color-text-secondary);">{{ matchResult.advice }}</p>
                </div>
            </div>

            <div class="result-footer" v-if="matchResult.token_usage">
                本次分析消耗: ¥{{ matchResult.token_usage.cost?.toFixed(4) || '0.0000' }}
            </div>
        </div>
    </div>
</template>

<style scoped>
.hero {
    text-align: center;
    margin-bottom: 40px;
}

.hero h1 {
    font-size: 2.5rem;
    margin-bottom: 12px;
}

.hero-desc {
    color: var(--color-text-secondary);
    font-size: 18px;
}

.match-form {
    max-width: 1000px;
    margin: 0 auto;
}

.match-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
}

@media (max-width: 768px) {
    .match-grid { grid-template-columns: 1fr; }
}

.match-section {
    background: var(--color-bg-card);
    padding: 24px;
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
}

.match-section h3 {
    margin-bottom: 16px;
    font-size: 16px;
}

.upload-hint {
    font-size: 12px;
    color: var(--color-text-muted);
    margin-top: 8px;
}

.divider {
    display: flex;
    align-items: center;
    margin: 16px 0;
    color: var(--color-text-muted);
    font-size: 12px;
}

.divider::before, .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--color-border);
}

.divider span {
    padding: 0 12px;
}

.match-submit {
    text-align: center;
    margin-top: 32px;
}

.match-hint {
    margin-top: 12px;
    font-size: 13px;
    color: var(--color-text-secondary);
}

.match-hint strong {
    color: var(--color-primary);
}

.error-message {
    background: rgba(239, 68, 68, 0.1);
    color: var(--color-danger);
    padding: 12px 16px;
    border-radius: var(--radius-md);
    margin-top: 16px;
    text-align: center;
}

.match-result {
    max-width: 1000px;
    margin: 40px auto 0;
    padding: 32px;
}

.result-footer {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid var(--color-border);
    text-align: right;
    font-size: 12px;
    color: var(--color-text-muted);
}

.login-hint { color: var(--color-text-muted); }
.login-link { color: var(--color-primary); text-decoration: none; font-weight: 500; }
.login-link:hover { text-decoration: underline; }
</style>
