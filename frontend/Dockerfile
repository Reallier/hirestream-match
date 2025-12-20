# TalentAI 前端 Dockerfile
FROM node:18 AS builder

WORKDIR /app

# 不再需要 apk add，Debian 自带通常足够的库，或者 apt-get

COPY package*.json ./
RUN npm install

# 复制源码
COPY . .

# 生成 Prisma Client
RUN npx prisma generate

# 构建应用
RUN npm run build

# Production
FROM node:18-slim AS production

WORKDIR /app

# 安装 OpenSSL (Prisma 需要)
RUN apt-get update -y && apt-get install -y openssl ca-certificates && rm -rf /var/lib/apt/lists/*

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
