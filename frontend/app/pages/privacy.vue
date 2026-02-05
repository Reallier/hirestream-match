<script setup lang="ts">
definePageMeta({ layout: 'default' });

useHead({
    title: '隐私政策 - TalentAI'
});
</script>

<template>
    <div class="container legal-page">
        <h1>隐私政策</h1>
        <p class="update-date">更新日期：2025年1月</p>

        <section>
            <h2>一、信息收集</h2>
            <p>TalentAI（以下简称"本服务"）在提供智能招聘匹配服务过程中，可能收集以下信息：</p>
            <h3>1.1 账户信息</h3>
            <ul>
                <li>通过简序智能官网注册时提供的邮箱、用户名</li>
                <li>第三方登录（如微信）授权的基本资料</li>
            </ul>
            <h3>1.2 业务数据</h3>
            <ul>
                <li><strong>简历信息</strong>：您上传的简历文件或输入的简历文本</li>
                <li><strong>职位描述</strong>：您输入的 JD 内容</li>
                <li><strong>匹配记录</strong>：分析结果、匹配评分</li>
            </ul>
            <h3>1.3 使用数据</h3>
            <ul>
                <li>服务使用记录、Token 消耗量、费用记录</li>
                <li>访问日志（IP 地址、浏览器信息、访问时间）</li>
            </ul>
        </section>

        <section>
            <h2>二、信息使用</h2>
            <p>我们收集的信息仅用于以下目的：</p>
            <ol>
                <li><strong>提供服务</strong>：处理简历匹配请求、生成分析报告</li>
                <li><strong>账户管理</strong>：用户认证、余额管理、使用统计</li>
                <li><strong>服务改进</strong>：分析使用模式以优化服务质量</li>
                <li><strong>安全保障</strong>：防止滥用、检测异常行为</li>
            </ol>
        </section>

        <section>
            <h2>三、信息存储与安全</h2>
            <h3>3.1 存储方式</h3>
            <ul>
                <li>数据存储于中国境内的云服务器</li>
                <li>传输过程采用 HTTPS 加密</li>
                <li>数据库采用访问控制和加密措施</li>
            </ul>
            <h3>3.2 保留期限</h3>
            <ul>
                <li>账户信息：账户存续期间及注销后 30 天</li>
                <li>简历数据：永久保留，用户可申请删除</li>
                <li>使用记录：永久保留，用于账单和审计</li>
            </ul>
        </section>

        <section>
            <h2>四、信息共享</h2>
            <p>我们<strong>不会</strong>向第三方出售、出租您的个人信息。</p>
            <p>以下情况除外：</p>
            <ul>
                <li><strong>AI 服务提供商</strong>：简历和 JD 文本会发送至阿里云通义千问 API 进行分析处理</li>
                <li><strong>法律要求</strong>：根据法律法规或政府部门要求</li>
            </ul>
        </section>

        <section>
            <h2>五、用户权利</h2>
            <p>您对个人信息享有以下权利：</p>
            <ul>
                <li><strong>访问权</strong>：查看我们持有的您的信息</li>
                <li><strong>更正权</strong>：更正不准确的信息</li>
                <li><strong>删除权</strong>：申请删除您的简历数据</li>
                <li><strong>撤回同意</strong>：停止使用服务并申请删除账户</li>
            </ul>
            <p>如需行使上述权利，请通过反馈功能或邮件联系我们。</p>
        </section>

        <section>
            <h2>六、Cookie 使用</h2>
            <p>本服务使用 Cookie 用于：</p>
            <ul>
                <li>保持登录状态</li>
                <li>记录用户偏好设置</li>
            </ul>
            <p>您可以通过浏览器设置管理 Cookie，但这可能影响服务的正常使用。</p>
        </section>

        <section>
            <h2>七、政策更新</h2>
            <p>我们可能不时更新本隐私政策。重大变更时，我们会在服务内进行通知。</p>
        </section>

        <section>
            <h2>八、联系我们</h2>
            <p>如有隐私相关问题，请通过以下方式联系：</p>
            <ul>
                <li>应用内反馈功能</li>
                <li>官网：<a href="https://intjtech.reallier.top:5443" target="_blank">intjtech.reallier.top</a></li>
            </ul>
        </section>
    </div>
</template>

<style scoped>
.legal-page {
    max-width: 800px;
    margin: 0 auto;
    padding: 40px 20px;
    line-height: 1.8;
}

.legal-page h1 {
    font-size: 2rem;
    margin-bottom: 8px;
}

.update-date {
    color: var(--color-text-muted);
    margin-bottom: 32px;
}

.legal-page section {
    margin-bottom: 32px;
}

.legal-page h2 {
    font-size: 1.25rem;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--color-border);
}

.legal-page h3 {
    font-size: 1rem;
    margin: 16px 0 8px;
}

.legal-page ul, .legal-page ol {
    padding-left: 24px;
    margin: 8px 0;
}

.legal-page li {
    margin: 4px 0;
}

.legal-page a {
    color: var(--color-primary);
}
</style>
