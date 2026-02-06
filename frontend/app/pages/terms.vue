<script setup lang="ts">
definePageMeta({ layout: 'default' });

useHead({
    title: '用户协议 - TalentAI'
});
</script>

<template>
    <div class="container legal-page">
        <h1>用户服务协议</h1>
        <p class="update-date">更新日期：2025年1月</p>

        <section>
            <h2>一、服务说明</h2>
            <p>TalentAI（以下简称"本服务"）是由简序智能（INTJTech）提供的智能招聘匹配工具。本服务利用人工智能技术分析简历与职位描述的匹配度，辅助用户进行招聘决策。</p>
            <p><strong>重要声明</strong>：本服务提供的匹配分析结果仅供参考，不应作为招聘决策的唯一依据。用户应结合实际情况做出判断。</p>
        </section>

        <section>
            <h2>二、账户与认证</h2>
            <ul>
                <li>本服务通过简序智能官网统一认证系统提供登录</li>
                <li>您需对账户安全负责，妥善保管登录凭据</li>
                <li>发现账户异常请立即联系我们</li>
            </ul>
        </section>

        <section>
            <h2>三、服务使用规范</h2>
            <h3>3.1 允许的使用</h3>
            <ul>
                <li>上传合法获取的简历进行匹配分析</li>
                <li>用于正当的招聘评估目的</li>
            </ul>
            <h3>3.2 禁止的行为</h3>
            <ul>
                <li>上传含有恶意代码或非法内容的文件</li>
                <li>尝试绕过系统限制或进行 API 滥用</li>
                <li>侵犯他人隐私权或知识产权</li>
                <li>将服务用于违法违规目的</li>
                <li>尝试逆向工程或破解服务</li>
            </ul>
        </section>

        <section>
            <h2>四、计费与付款</h2>
            <h3>4.1 计费模式</h3>
            <ul>
                <li>服务按 Token 消耗量计费</li>
                <li>系统会在分析完成后自动扣减余额</li>
                <li>各功能的具体费用可在服务内查看</li>
            </ul>
            <h3>4.2 免费额度</h3>
            <ul>
                <li>新用户可能获得一定免费额度（具体以活动为准）</li>
                <li>免费额度不可提现，可能设有有效期</li>
            </ul>
            <h3>4.3 充值与退款</h3>
            <ul>
                <li>充值后余额可用于本服务消费</li>
                <li>已消费金额不予退还</li>
                <li>账户注销前请确保余额已使用完毕</li>
            </ul>
        </section>

        <section>
            <h2>五、数据与隐私</h2>
            <p>我们重视您的隐私。有关数据收集、使用和保护的详细信息，请参阅 
                <NuxtLink to="/privacy">《隐私政策》</NuxtLink>。
            </p>
            <p>特别说明：</p>
            <ul>
                <li>您上传的简历内容会被发送至 AI 服务进行分析</li>
                <li>我们不会将您的数据用于训练 AI 模型</li>
                <li>您可随时申请删除个人数据</li>
            </ul>
        </section>

        <section>
            <h2>六、免责声明</h2>
            <ul>
                <li><strong>结果参考性</strong>：AI 分析结果仅供参考，不保证 100% 准确</li>
                <li><strong>服务可用性</strong>：我们努力保障服务稳定，但不承诺 100% 可用</li>
                <li><strong>第三方依赖</strong>：服务依赖阿里云 AI 接口，其不可用可能影响本服务</li>
                <li><strong>用户行为</strong>：用户须对上传内容的合法性负责</li>
            </ul>
        </section>

        <section>
            <h2>七、知识产权</h2>
            <ul>
                <li>本服务的界面、代码、算法等归简序智能所有</li>
                <li>用户上传的简历内容归用户所有</li>
                <li>服务生成的分析报告用户有权使用</li>
            </ul>
        </section>

        <section>
            <h2>八、协议变更</h2>
            <p>我们可能根据法律法规或业务需要更新本协议。重大变更时将通过服务内通知或其他方式告知您。继续使用服务即表示接受变更后的协议。</p>
        </section>

        <section>
            <h2>九、争议解决</h2>
            <p>本协议的解释和执行适用中华人民共和国法律。如发生争议，双方应友好协商解决；协商不成的，提交被告所在地人民法院管辖。</p>
        </section>

        <section>
            <h2>十、联系方式</h2>
            <p>如有疑问，请通过以下方式联系：</p>
            <ul>
                <li>应用内反馈功能</li>
                <li>官网：<a href="https://www.intjsys.com" target="_blank">www.intjsys.com</a></li>
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
