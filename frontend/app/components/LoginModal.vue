<script setup lang="ts">
/**
 * TalentAI 登录 Modal
 * 邮箱 + 验证码登录（与官网一致）
 */
import { ref, watch, computed } from 'vue';

const { loginWithEmail, refreshUser } = useAuth();
const runtimeConfig = useRuntimeConfig();

const props = defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'success'): void;
}>();

// 表单状态
const email = ref('');
const code = ref('');
const step = ref<'email' | 'code'>('email');

// 加载状态
const loading = ref(false);
const sendingCode = ref(false);
const error = ref('');

// 倒计时
const countdown = ref(0);
let countdownTimer: NodeJS.Timeout | null = null;

const canSendCode = computed(() => {
  return email.value && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value) && countdown.value === 0;
});

// 关闭 Modal
const closeModal = () => {
  emit('update:modelValue', false);
  // 重置状态
  setTimeout(() => {
    email.value = '';
    code.value = '';
    step.value = 'email';
    error.value = '';
    countdown.value = 0;
    if (countdownTimer) {
      clearInterval(countdownTimer);
      countdownTimer = null;
    }
  }, 200);
};

// 发送验证码
const handleSendCode = async () => {
  if (!canSendCode.value || sendingCode.value) return;
  
  sendingCode.value = true;
  error.value = '';

  try {
    const apiBase = runtimeConfig.public.apiBase;
    const response = await $fetch<{ success: boolean; message: string }>(`${apiBase}/api/auth/email/send`, {
      method: 'POST',
      body: { email: email.value },
      credentials: 'include'
    });

    if (response.success) {
      step.value = 'code';
      // 开始倒计时
      countdown.value = 60;
      countdownTimer = setInterval(() => {
        countdown.value--;
        if (countdown.value <= 0) {
          clearInterval(countdownTimer!);
          countdownTimer = null;
        }
      }, 1000);
    } else {
      error.value = response.message || '发送失败';
    }
  } catch (e: any) {
    console.error('Send code error:', e);
    error.value = e.data?.message || e.message || '发送失败，请稍后重试';
  } finally {
    sendingCode.value = false;
  }
};

// 验证并登录
const handleVerify = async () => {
  if (!code.value || code.value.length !== 6) {
    error.value = '请输入6位验证码';
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    const apiBase = runtimeConfig.public.apiBase;
    const response = await $fetch<{ success: boolean; message: string; user: any }>(`${apiBase}/api/auth/email/verify`, {
      method: 'POST',
      body: { email: email.value, code: code.value },
      credentials: 'include'
    });

    if (response.success) {
      // 刷新用户状态
      await refreshUser();
      closeModal();
      emit('success');
    } else {
      error.value = response.message || '验证失败';
    }
  } catch (e: any) {
    console.error('Verify error:', e);
    error.value = e.data?.message || e.message || '验证失败，请稍后重试';
  } finally {
    loading.value = false;
  }
};

// 返回上一步
const goBack = () => {
  step.value = 'email';
  code.value = '';
  error.value = '';
};

// 点击遮罩关闭
const handleOverlayClick = (e: MouseEvent) => {
  if ((e.target as HTMLElement).classList.contains('modal-overlay')) {
    closeModal();
  }
};

// ESC 键关闭
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape' && props.modelValue) {
    closeModal();
  }
};

// 监听键盘事件和 body 滚动
if (typeof window !== 'undefined') {
  watch(() => props.modelValue, (visible) => {
    if (visible) {
      document.addEventListener('keydown', handleKeydown);
      document.body.style.overflow = 'hidden';
    } else {
      document.removeEventListener('keydown', handleKeydown);
      document.body.style.overflow = '';
    }
  });
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="modelValue" class="modal-overlay" @click="handleOverlayClick">
        <div class="modal-container">
          <!-- 关闭按钮 -->
          <button class="modal-close" @click="closeModal" type="button">
            <FaIcon icon="times" />
          </button>

          <!-- Modal 内容 -->
          <div class="modal-content">
            <div class="modal-header">
              <h2 class="modal-title">登录 TalentAI</h2>
              <p class="modal-subtitle">使用邮箱验证码登录</p>
            </div>

            <!-- 邮箱输入步骤 -->
            <form v-if="step === 'email'" @submit.prevent="handleSendCode" class="login-form">
              <div class="form-group">
                <label class="form-label">邮箱地址</label>
                <input 
                  v-model="email" 
                  type="email" 
                  placeholder="请输入邮箱"
                  :disabled="sendingCode"
                  autocomplete="email"
                  class="form-input"
                />
              </div>

              <div v-if="error" class="error-message">
                <FaIcon icon="exclamation-circle" style="margin-right: 6px;" />
                {{ error }}
              </div>

              <button 
                type="submit" 
                class="btn btn-primary btn-block" 
                :disabled="!canSendCode || sendingCode"
              >
                <span v-if="sendingCode" class="loading-spinner"></span>
                <span v-else>获取验证码</span>
              </button>
            </form>

            <!-- 验证码输入步骤 -->
            <form v-else @submit.prevent="handleVerify" class="login-form">
              <div class="step-info">
                <button type="button" class="back-btn" @click="goBack">
                  <FaIcon icon="arrow-left" />
                </button>
                <span class="email-hint">验证码已发送至 {{ email }}</span>
              </div>

              <div class="form-group">
                <label class="form-label">验证码</label>
                <input 
                  v-model="code" 
                  type="text" 
                  inputmode="numeric"
                  pattern="[0-9]*"
                  maxlength="6"
                  placeholder="请输入6位验证码"
                  :disabled="loading"
                  autocomplete="one-time-code"
                  class="form-input code-input"
                />
              </div>

              <div v-if="error" class="error-message">
                <FaIcon icon="exclamation-circle" style="margin-right: 6px;" />
                {{ error }}
              </div>

              <button type="submit" class="btn btn-primary btn-block" :disabled="loading || code.length !== 6">
                <span v-if="loading" class="loading-spinner"></span>
                <span v-else>登录</span>
              </button>

              <button 
                type="button" 
                class="resend-btn" 
                :disabled="countdown > 0 || sendingCode"
                @click="handleSendCode"
              >
                <span v-if="countdown > 0">{{ countdown }}s 后可重新发送</span>
                <span v-else-if="sendingCode">发送中...</span>
                <span v-else>重新发送验证码</span>
              </button>
            </form>

            <p class="register-hint">
              首次登录将自动注册账号
            </p>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* Modal 遮罩 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 20px;
}

/* Modal 容器 */
.modal-container {
  position: relative;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  width: 100%;
  max-width: 420px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

/* 关闭按钮 */
.modal-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.modal-close:hover {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}

/* Modal 内容 */
.modal-content {
  padding: 48px 40px 40px;
}

.modal-header {
  text-align: center;
  margin-bottom: 32px;
}

.modal-title {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text);
  margin: 0 0 8px;
}

.modal-subtitle {
  font-size: 14px;
  color: var(--color-text-secondary);
  margin: 0;
}

/* 表单样式 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: 15px;
  background: var(--color-bg);
  color: var(--color-text);
  transition: border-color 0.2s;
  box-sizing: border-box;
  font-family: inherit;
}

.form-input:focus {
  outline: none;
  border-color: var(--color-primary);
}

.form-input:disabled {
  background: var(--color-bg-secondary);
  cursor: not-allowed;
}

/* 验证码输入框居中大字体 */
.code-input {
  font-size: 24px;
  letter-spacing: 8px;
  text-align: center;
  font-family: monospace;
}

/* 步骤信息 */
.step-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.back-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.back-btn:hover {
  background: var(--color-bg);
  color: var(--color-text);
}

.email-hint {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* 错误消息 */
.error-message {
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: var(--radius-md);
  color: var(--color-danger);
  font-size: 14px;
}

/* 提交按钮 */
.btn-block {
  width: 100%;
}

/* 重新发送按钮 */
.resend-btn {
  background: transparent;
  border: none;
  color: var(--color-primary);
  font-size: 14px;
  cursor: pointer;
  padding: 8px;
  text-align: center;
}

.resend-btn:disabled {
  color: var(--color-text-muted);
  cursor: not-allowed;
}

.resend-btn:not(:disabled):hover {
  text-decoration: underline;
}

/* 注册提示 */
.register-hint {
  margin-top: 24px;
  font-size: 13px;
  color: var(--color-text-muted);
  text-align: center;
}

/* Loading 样式 */
.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 过渡动画 */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.25s ease;
}

.modal-enter-active .modal-container,
.modal-leave-active .modal-container {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-container,
.modal-leave-to .modal-container {
  transform: translateY(-20px);
  opacity: 0;
}
</style>
