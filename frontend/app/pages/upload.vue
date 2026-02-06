<script setup lang="ts">
/**
 * 简历上传入库页面
 * 
 * 调用后端 FastAPI 服务
 */
definePageMeta({ layout: 'default' });

const { user, refreshUser, redirectToLogin } = useAuth();
const { uploadResume } = useCandidates();

// 状态
const files = ref<File[]>([]);
const isDragging = ref(false);
const isUploading = ref(false);
const uploadProgress = ref(0);
const uploadResults = ref<any[]>([]);
const errorMessage = ref('');

// 拖拽处理
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
    if (e.dataTransfer?.files) {
        addFiles(Array.from(e.dataTransfer.files));
    }
};

// 文件选择
const fileInput = ref<HTMLInputElement | null>(null);

const handleFileSelect = (event: Event) => {
    const input = event.target as HTMLInputElement;
    if (input.files) {
        addFiles(Array.from(input.files));
    }
};

const addFiles = (newFiles: File[]) => {
    // 支持 PDF 和图片格式（通过扩展名和 MIME 类型判断）
    const validExtensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.webp'];
    const validFiles = newFiles.filter(f => {
        const ext = f.name.toLowerCase().substring(f.name.lastIndexOf('.'));
        const isValidExt = validExtensions.includes(ext);
        const isValidMime = f.type === 'application/pdf' || f.type.startsWith('image/');
        // 如果 MIME 类型为空（某些拖拽场景），仅用扩展名判断
        return isValidExt || isValidMime;
    });
    
    if (validFiles.length === 0 && newFiles.length > 0) {
        errorMessage.value = '不支持的文件格式，请上传 PDF 或图片文件';
    }
    
    files.value = [...files.value, ...validFiles];
};

const removeFile = (index: number) => {
    files.value.splice(index, 1);
};

// 上传处理
const totalFiles = ref(0);

const uploadFiles = async () => {
    if (!user.value) {
        redirectToLogin();
        return;
    }

    if (files.value.length === 0) {
        errorMessage.value = '请选择至少一个文件';
        return;
    }

    isUploading.value = true;
    errorMessage.value = '';
    uploadResults.value = [];
    uploadProgress.value = 0;

    const filesToUpload = [...files.value]; // 复制一份，避免循环中被修改
    totalFiles.value = filesToUpload.length;
    let completed = 0;

    for (const file of filesToUpload) {
        const result = await uploadResume(file);

        if (result.success) {
            uploadResults.value.push({
                filename: file.name,
                success: true,
                candidate: result.candidate
            });
        } else {
            uploadResults.value.push({
                filename: file.name,
                success: false,
                error: result.message || '上传失败'
            });
        }
        
        completed++;
        uploadProgress.value = Math.round((completed / totalFiles.value) * 100);
    }

    isUploading.value = false;
    files.value = [];
    totalFiles.value = 0;
    await refreshUser();
};

const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
};
</script>

<template>
    <div class="container">
        <section class="hero">
            <h1><FaIcon icon="cloud-upload-alt" style="margin-right: 12px;" />简历入库</h1>
            <p class="hero-desc">上传简历到您的专属人才库，支持批量上传</p>
        </section>

        <!-- 未登录提示 -->
        <div v-if="!user" class="login-notice">
            <p><FaIcon icon="sign-in-alt" style="margin-right: 6px;" />请先登录后使用简历入库功能</p>
            <button class="btn btn-primary" @click="redirectToLogin">立即登录</button>
        </div>

        <!-- 上传区域 -->
        <div v-else class="upload-container">
            <div 
                class="upload-zone"
                :class="{ dragover: isDragging, 'has-files': files.length > 0 }"
                @click="fileInput?.click()"
                @dragover="handleDragOver"
                @dragleave="handleDragLeave"
                @drop="handleDrop"
            >
                <div class="upload-icon"><FaIcon icon="folder-open" /></div>
                <p class="upload-title">点击或拖拽文件到此处</p>
                <p class="upload-hint">支持 PDF、图片格式，可同时上传多个文件</p>
            </div>
            <input 
                ref="fileInput"
                type="file" 
                accept=".pdf,.jpg,.jpeg,.png,.gif,.webp"
                multiple
                style="display: none;"
                @change="handleFileSelect"
            />

            <!-- 文件列表 -->
            <div v-if="files.length > 0" class="file-list">
                <h3>待上传文件 ({{ files.length }})</h3>
                <div class="file-item" v-for="(file, i) in files" :key="i">
                    <div class="file-info">
                        <span class="file-icon"><FaIcon icon="file-alt" /></span>
                        <span class="file-name">{{ file.name }}</span>
                        <span class="file-size">{{ formatFileSize(file.size) }}</span>
                    </div>
                    <button class="file-remove" @click.stop="removeFile(i)"><FaIcon icon="times" /></button>
                </div>
            </div>

            <!-- 错误提示 -->
            <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>

            <!-- 上传按钮 -->
            <div class="upload-actions">
            <button 
                    class="btn btn-primary btn-lg" 
                    @click="uploadFiles"
                    :disabled="isUploading || files.length === 0"
                >
                    <span v-if="isUploading" class="loading-spinner"></span>
                    {{ isUploading ? (totalFiles > 1 ? `上传中 ${uploadProgress}%` : '正在解析入库...') : '开始上传入库' }}
                </button>
            </div>

            <!-- 上传结果 -->
            <div v-if="uploadResults.length > 0" class="upload-results">
                <h3>上传结果</h3>
                <div 
                    class="result-item" 
                    v-for="(result, i) in uploadResults" 
                    :key="i"
                    :class="{ success: result.success, error: !result.success }"
                >
                    <span class="result-icon"><FaIcon :icon="result.success ? 'check-circle' : 'times-circle'" /></span>
                    <span class="result-name">{{ result.filename }}</span>
                    <span v-if="result.success && result.candidate" class="result-info">
                        → {{ result.candidate.name || '未识别姓名' }}
                    </span>
                    <span v-else-if="!result.success" class="result-error">{{ result.error }}</span>
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

.upload-container {
    max-width: 700px;
    margin: 0 auto;
}

.upload-zone {
    border: 2px dashed var(--color-border);
    border-radius: var(--radius-lg);
    padding: 60px 40px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
}

.upload-zone:hover, .upload-zone.dragover {
    border-color: var(--color-primary);
    background: rgba(37, 99, 235, 0.02);
}

.upload-icon { font-size: 48px; margin-bottom: 16px; }
.upload-title { font-size: 18px; font-weight: 500; margin-bottom: 8px; }
.upload-hint { font-size: 14px; color: var(--color-text-muted); }

.file-list {
    margin-top: 24px;
    background: var(--color-bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
    padding: 20px;
}

.file-list h3 { font-size: 14px; margin-bottom: 16px; }

.file-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    background: var(--color-bg);
    border-radius: var(--radius-md);
    margin-bottom: 8px;
}

.file-info { display: flex; align-items: center; gap: 12px; }
.file-icon { font-size: 20px; }
.file-name { font-weight: 500; }
.file-size { font-size: 12px; color: var(--color-text-muted); }
.file-remove {
    background: none;
    border: none;
    color: var(--color-text-muted);
    cursor: pointer;
    font-size: 16px;
}
.file-remove:hover { color: var(--color-danger); }

.upload-actions {
    margin-top: 24px;
    text-align: center;
}

.error-message {
    background: rgba(239, 68, 68, 0.1);
    color: var(--color-danger);
    padding: 12px 16px;
    border-radius: var(--radius-md);
    margin-top: 16px;
    text-align: center;
}

.upload-results {
    margin-top: 24px;
    background: var(--color-bg-card);
    border-radius: var(--radius-lg);
    border: 1px solid var(--color-border);
    padding: 20px;
}

.upload-results h3 { font-size: 14px; margin-bottom: 16px; }

.result-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border-radius: var(--radius-md);
    margin-bottom: 8px;
}

.result-item.success { background: rgba(16, 185, 129, 0.1); }
.result-item.error { background: rgba(239, 68, 68, 0.1); }
.result-icon { font-size: 18px; }
.result-name { font-weight: 500; }
.result-info { color: var(--color-success); font-size: 13px; }
.result-error { color: var(--color-danger); font-size: 13px; }
</style>
