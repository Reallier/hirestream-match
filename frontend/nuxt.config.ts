// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-11-01',
  devtools: { enabled: true },

  // 指定源码目录结构
  serverDir: 'app/server',

  css: ['@/assets/css/main.css'],

  app: {
    head: {
      title: 'TalentAI - 智能招聘匹配系统',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: '基于 AI 的智能简历匹配与招聘管理系统' }
      ],
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap' }
      ]
    }
  },

  runtimeConfig: {
    jwtSecret: process.env.JWT_SECRET || 'development-secret',
    dashscopeApiKey: process.env.DASHSCOPE_API_KEY || '',
    public: {
      apiBase: process.env.TALENTAI_API_URL || 'http://localhost:8000'
    }
  },

  nitro: {
    preset: 'node-server'
  }
})
