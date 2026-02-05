# TalentAI 前端 Dockerfile (优化版)
FROM node:22 AS builder

WORKDIR /app

# 先复制依赖文件并安装（利用 Docker 缓存）
COPY package.json package-lock.json* ./
RUN npm ci || npm install

# 复制 Prisma schema
COPY prisma ./prisma
RUN npx prisma generate

# 复制源码并构建
COPY . .
RUN npm run build

# Production (精简镜像)
FROM node:22-slim AS production

WORKDIR /app

# 安装 OpenSSL (Prisma 需要)
RUN apt-get update -y && apt-get install -y openssl ca-certificates && rm -rf /var/lib/apt/lists/*

# 直接从 builder 复制已生成的 Prisma Client
COPY --from=builder /app/.output ./.output
COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
COPY --from=builder /app/node_modules/@prisma ./node_modules/@prisma

ENV NODE_ENV=production
ENV NITRO_HOST=0.0.0.0
ENV NITRO_PORT=3000

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]
