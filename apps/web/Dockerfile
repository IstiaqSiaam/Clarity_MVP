FROM node:20-alpine
WORKDIR /app
COPY package.json pnpm-lock.yaml* ./
RUN corepack enable && corepack prepare pnpm@latest --activate || npm i -g pnpm
RUN pnpm install
COPY . .
EXPOSE 3000
CMD ["pnpm", "dev", "--port", "3000", "--hostname", "0.0.0.0"]
