# Multi-stage build for faster rebuilds
FROM node:18-alpine AS base

WORKDIR /app

# Install build dependencies (cached layer)
RUN apk add --no-cache python3 make g++

# Dependencies stage (cached unless package.json changes)
FROM base AS dependencies
COPY package*.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --legacy-peer-deps --ignore-scripts

# Build stage (only rebuilds when source changes)
FROM dependencies AS builder
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
