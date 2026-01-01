<script setup lang="ts">
/**
 * TalentAI 登录 Modal
 * 本地登录，使用官网统一认证
 */
import { ref, watch } from 'vue';

const props = defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
  (e: 'success'): void;
}>();

const form = ref({
  username: '',
  password: ''
});

const loading = ref(false);
const error = ref('');

// 关闭 Modal
const closeModal = () => {
  emit('update:modelValue', false);
  error.value = '';
  form.value = { username: '', password: '' };
};

// 处理登录
const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    error.value = '请输入用户名和密码';
    return;
  }

  loading.value = true;
  error.value = '';

  try {
    // 调用本地 API 进行登录（由后端代理到官网认证）
    const response = await $fetch<{ success: boolean; message?: string }>('/api/auth/login', {
      method: 'POST',
      body: {
        username: form.value.username,
        password: form.value.password
      }
    });

    if (response.success) {
      closeModal();
      emit('success');
    } else {
      error.value = response.message || '登录失败';
    }
  } catch (e: any) {
    console.error('Login error:', e);
    error.value = e.data?.message || '登录失败，请稍后重试';
  } finally {
    loading.value = false;
  }
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
              <p class="modal-subtitle">使用您的简序智能账号</p>
            </div>

            <form @submit.prevent="handleLogin" class="login-form">
              <div class="form-group">
                <label class="form-label">用户名</label>
                <input 
                  v-model="form.username" 
                  type="text" 
                  placeholder="请输入用户名"
                  :disabled="loading"
                  autocomplete="username"
                  class="form-input"
                />
              </div>

              <div class="form-group">
                <label class="form-label">密码</label>
                <input 
                  v-model="form.password" 
                  type="password" 
                  placeholder="请输入密码"
                  :disabled="loading"
                  autocomplete="current-password"
                  class="form-input"
                />
              </div>

              <div v-if="error" class="error-message">
                <FaIcon icon="exclamation-circle" style="margin-right: 6px;" />
                {{ error }}
              </div>

              <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
                <span v-if="loading" class="loading-spinner"></span>
                <span v-else>登录</span>
              </button>
            </form>

            <p class="register-hint">
              暂不支持自助注册，请联系管理员开通账号
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

/* 注册提示 */
.register-hint {
  margin-top: 24px;
  font-size: 13px;
  color: var(--color-text-muted);
  text-align: center;
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
</CodeContent>
<parameter name="Complexity">4
