FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# --- Dev target ---
FROM deps AS dev
COPY . .
CMD ["npm", "run", "dev"]

# --- Build ---
FROM deps AS builder
COPY . .
ENV NEXT_PUBLIC_API_URL=/api/v1
ENV NEXT_PUBLIC_WS_URL=wss://jarvis.pmai.space/api/v1/ws/chat
ENV NEXT_PUBLIC_GOOGLE_CLIENT_ID=820597896287-ui375qvmgov4g645a7j2ndseov4jl4sc.apps.googleusercontent.com
RUN npm run build

# --- Prod target ---
FROM node:22-alpine AS prod
WORKDIR /app
RUN addgroup --system --gid 1001 nodejs && adduser --system --uid 1001 nextjs
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
USER nextjs
ENV HOSTNAME=0.0.0.0 PORT=3000
CMD ["node", "server.js"]
