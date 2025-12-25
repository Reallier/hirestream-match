<script setup lang="ts">
/**
 * 反馈组件 - 浮动按钮 + 弹窗表单
 */
const isOpen = ref(false);
const isSubmitting = ref(false);
const submitted = ref(false);

const form = ref({
    type: 'suggestion',
    content: '',
    contact: ''
});

const typeOptions = [
    { value: 'suggestion', label: '功能建议' },
    { value: 'bug', label: '问题反馈' },
    { value: 'other', label: '其他' }
];

const submit = async () => {
    if (!form.value.content.trim()) {
        return;
    }

    isSubmitting.value = true;
    try {
        await $fetch('/api/feedback/submit', {
            method: 'POST',
            body: {
                type: form.value.type,
                content: form.value.content,
                contact: form.value.contact,
                page: window.location.pathname
            }
        });
        submitted.value = true;
        // 3秒后关闭
        setTimeout(() => {
            isOpen.value = false;
            submitted.value = false;
            form.value = { type: 'suggestion', content: '', contact: '' };
        }, 2500);
    } catch (error) {
        console.error('Feedback submit error:', error);
    } finally {
        isSubmitting.value = false;
    }
};

const close = () => {
    isOpen.value = false;
    submitted.value = false;
};
</script>

<template>
    <!-- 浮动按钮 -->
    <button 
        class="feedback-fab" 
        @click="isOpen = true"
        title="反馈建议"
    >
        <FaIcon icon="comment-alt" />
    </button>

    <!-- 反馈弹窗 -->
    <Teleport to="body">
        <div v-if="isOpen" class="feedback-overlay" @click.self="close">
            <div class="feedback-modal">
                <div class="feedback-header">
                    <h3><FaIcon icon="comment-alt" style="margin-right: 8px;" />反馈建议</h3>
                    <button class="feedback-close" @click="close">
                        <FaIcon icon="times" />
                    </button>
                </div>

                <div v-if="submitted" class="feedback-success">
                    <FaIcon icon="check-circle" style="font-size: 48px; color: var(--color-success);" />
                    <p>感谢您的反馈！</p>
                    <p class="feedback-success-sub">我们会认真阅读每一条建议</p>
                </div>

                <div v-else class="feedback-body">
                    <div class="feedback-field">
                        <label>反馈类型</label>
                        <div class="feedback-types">
                            <label 
                                v-for="opt in typeOptions" 
                                :key="opt.value"
                                class="feedback-type-option"
                                :class="{ active: form.type === opt.value }"
                            >
                                <input 
                                    type="radio" 
                                    :value="opt.value" 
                                    v-model="form.type"
                                />
                                {{ opt.label }}
                            </label>
                        </div>
                    </div>

                    <div class="feedback-field">
                        <label>反馈内容 <span class="required">*</span></label>
                        <textarea 
                            v-model="form.content"
                            placeholder="请描述您的建议或遇到的问题..."
                            rows="4"
                        ></textarea>
                    </div>

                    <div class="feedback-field">
                        <label>联系方式 <span class="optional">(可选)</span></label>
                        <input 
                            v-model="form.contact"
                            type="text"
                            placeholder="邮箱或微信，方便我们回复您"
                        />
                    </div>

                    <button 
                        class="feedback-submit"
                        @click="submit"
                        :disabled="isSubmitting || !form.content.trim()"
                    >
                        <span v-if="isSubmitting" class="loading-spinner"></span>
                        {{ isSubmitting ? '提交中...' : '提交反馈' }}
                    </button>
                </div>
            </div>
        </div>
    </Teleport>
</template>

<style scoped>
.feedback-fab {
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 52px;
    height: 52px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--color-primary), var(--color-primary-light));
    color: white;
    border: none;
    font-size: 20px;
    cursor: pointer;
    box-shadow: 0 4px 16px rgba(37, 99, 235, 0.3);
    transition: all 0.2s;
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.feedback-fab:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 24px rgba(37, 99, 235, 0.4);
}

.feedback-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1001;
    animation: fadeIn 0.2s;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

.feedback-modal {
    background: var(--color-bg-card);
    border-radius: var(--radius-lg);
    width: 100%;
    max-width: 420px;
    margin: 20px;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
    animation: slideUp 0.3s;
}

@keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

.feedback-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 20px 24px;
    border-bottom: 1px solid var(--color-border);
}

.feedback-header h3 {
    margin: 0;
    font-size: 18px;
}

.feedback-close {
    background: none;
    border: none;
    font-size: 18px;
    color: var(--color-text-muted);
    cursor: pointer;
    padding: 4px;
}

.feedback-close:hover {
    color: var(--color-text);
}

.feedback-body {
    padding: 24px;
}

.feedback-field {
    margin-bottom: 20px;
}

.feedback-field label {
    display: block;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 8px;
}

.required { color: var(--color-danger); }
.optional { color: var(--color-text-muted); font-weight: 400; }

.feedback-types {
    display: flex;
    gap: 8px;
}

.feedback-type-option {
    flex: 1;
    padding: 10px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    text-align: center;
    cursor: pointer;
    font-size: 13px;
    transition: all 0.2s;
}

.feedback-type-option input {
    display: none;
}

.feedback-type-option:hover {
    border-color: var(--color-primary);
}

.feedback-type-option.active {
    background: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
}

.feedback-body textarea,
.feedback-body input {
    width: 100%;
    padding: 12px;
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    font-size: 14px;
    resize: vertical;
    box-sizing: border-box;
}

.feedback-body textarea:focus,
.feedback-body input:focus {
    outline: none;
    border-color: var(--color-primary);
}

.feedback-submit {
    width: 100%;
    padding: 14px;
    background: var(--color-primary);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    font-size: 15px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
}

.feedback-submit:hover:not(:disabled) {
    background: var(--color-primary-dark);
}

.feedback-submit:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.feedback-success {
    padding: 48px 24px;
    text-align: center;
}

.feedback-success p {
    margin: 16px 0 0;
    font-size: 18px;
    font-weight: 500;
}

.feedback-success-sub {
    color: var(--color-text-secondary);
    font-size: 14px !important;
    font-weight: 400 !important;
}
</style>
