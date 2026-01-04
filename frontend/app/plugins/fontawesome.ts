/**
 * Font Awesome 插件
 * 注册常用图标到全局
 */
import { library } from '@fortawesome/fontawesome-svg-core'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'
import {
    faBolt,           // ⚡ 即时匹配
    faFileAlt,        // 📄 简历入库
    faUsers,          // 📊 人才库
    faSearch,         // 🔍 搜索
    faBullseye,       // 🎯 JD匹配
    faHistory,        // 📜 历史
    faWallet,         // 💰 余额
    faUpload,         // 上传
    faTrash,          // 删除
    faCheck,          // 成功
    faTimes,          // 关闭
    faSpinner,        // 加载
    faUser,           // 用户
    faEnvelope,       // 邮件
    faPhone,          // 电话
    faMapMarkerAlt,   // 位置
    faBriefcase,      // 工作
    faBuilding,       // 公司
    faGraduationCap,  // 教育
    faStar,           // 星星/评分
    faChevronRight,   // 箭头
    faChevronDown,    // 下拉箭头
    faPlus,           // 添加
    faMinus,          // 减少
    faEdit,           // 编辑
    faEye,            // 查看
    faDownload,       // 下载
    faCopy,           // 复制
    faExclamationTriangle, // 警告
    faInfoCircle,     // 信息
    faCheckCircle,    // 成功圆形
    faTimesCircle,    // 错误圆形
    faSignInAlt,      // 登录
    faSignOutAlt,     // 登出
    faCog,            // 设置
    faCloudUploadAlt, // 云上传
    faFileUpload,     // 文件上传
    faChartBar,       // 图表
    faFolderOpen,     // 文件夹
    faCalendar,       // 日历
    faComment,        // 💬 反馈（替代 comment-alt）
    faLock,           // 🔒 权限
    faInbox,          // 📥 空状态
} from '@fortawesome/free-solid-svg-icons'

// 注册图标到库
library.add(
    faBolt, faFileAlt, faUsers, faSearch, faBullseye, faHistory,
    faWallet, faUpload, faTrash, faCheck, faTimes, faSpinner,
    faUser, faEnvelope, faPhone, faMapMarkerAlt, faBriefcase, faBuilding,
    faGraduationCap, faStar, faChevronRight, faChevronDown, faPlus, faMinus,
    faEdit, faEye, faDownload, faCopy, faExclamationTriangle, faInfoCircle,
    faCheckCircle, faTimesCircle, faSignInAlt, faSignOutAlt, faCog,
    faCloudUploadAlt, faFileUpload, faChartBar, faFolderOpen, faCalendar,
    faComment, faLock, faInbox
)

export default defineNuxtPlugin((nuxtApp) => {
    nuxtApp.vueApp.component('FontAwesomeIcon', FontAwesomeIcon)
    // 简写别名
    nuxtApp.vueApp.component('FaIcon', FontAwesomeIcon)
})
