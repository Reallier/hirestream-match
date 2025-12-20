# TalentAI 前端 Dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

# 安装依赖
RUN apk add --no-cache openssl libc6-compat

COPY package*.json ./
RUN npm install

# 复制源码
COPY . .

# 生成 Prisma Client
RUN npx prisma generate

# 构建应用
RUN npm run build

# Production
FROM node:18-alpine AS production

WORKDIR /app

RUN apk add --no-cache openssl libc6-compat

# 复制构建产物
COPY --from=builder /app/.output ./.output
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/prisma ./prisma

# 生成 Prisma Client（生产环境）
RUN npm install @prisma/client && npx prisma generate

ENV NODE_ENV=production
ENV NITRO_HOST=0.0.0.0
ENV NITRO_PORT=3000

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
